"""
Agent API Router.

Handles endpoints for conversational AI agent for video editing assistance.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict

from models.requests.AgentRequest import AgentRequest
from models.responses.AgentResponse import AgentResponse
from business_logic.invoke_agent import AgentService
from core.dependencies import get_agent_service, resolve_chat_provider
from core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Agent"])


@router.post("/chat", response_model=AgentResponse)
async def agent_chat(request: AgentRequest, user: Dict = Depends(get_current_user)) -> AgentResponse:
    user_id = user.get("user_id")
    session_id = user.get("session_id")

    if not user_id or not session_id:
        logger.error("Invalid JWT: missing user_id or session_id")
        raise HTTPException(status_code=400, detail="Invalid JWT: missing user_id or session_id")

    chat_provider, _ = resolve_chat_provider(request.provider, None)
    service = AgentService(chat_provider=chat_provider)

    try:
        import json

        if not request.messages or len(request.messages) == 0:
            raise HTTPException(status_code=400, detail="No messages provided in conversation")

        conversation_history = []
        for msg in request.messages:
            role = None
            content = msg.content
            if getattr(msg, 'sender', None):
                s = msg.sender
                if s == 'user':
                    role = 'user'
                elif s == 'assistant':
                    role = 'assistant'
                elif s == 'system':
                    role = 'system'
                elif s == 'tool':
                    role = 'tool'
                else:
                    role = 'user'
            else:
                role = 'user' if msg.isUser else 'assistant'

            conversation_history.append({"role": role, "content": content})

        composition_json = None
        if request.currentComposition:
            composition_json = json.dumps(request.currentComposition, indent=2)

        media_library = None
        if request.mediaLibrary:
            media_library = [
                {
                    "name": media.get("name"),
                    "url": media.get("gcsUri") or media.get("mediaUrlRemote"),
                    "type": media.get("mediaType"),
                }
                for media in request.mediaLibrary
                if media.get("name") and (media.get("gcsUri") or media.get("mediaUrlRemote"))
            ]

        result = await service.chat(
            conversation_history=conversation_history,
            composition_json=composition_json,
            media_library=media_library,
            duration=request.compositionDuration,
            user_id=user_id,
            session_id=session_id,
        )

        return AgentResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in agent_chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/capabilities")
async def get_agent_capabilities(service: AgentService = Depends(get_agent_service)) -> Dict:
    try:
        capabilities = await service.get_capabilities()
        return capabilities
    except Exception as e:
        logger.error(f"Error getting agent capabilities: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent capabilities: {str(e)}")
