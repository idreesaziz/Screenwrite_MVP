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
from core.dependencies import get_agent_service
from core.security import get_current_user

logger = logging.getLogger(__name__)

# Create router without prefix (prefix is added in main.py)
router = APIRouter(
    tags=["Agent"]
)


@router.post("/chat", response_model=AgentResponse)
async def agent_chat(
    request: AgentRequest,
    user: Dict = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service)
) -> AgentResponse:
    """
    Chat with the AI video editing agent.
    
    The agent provides conversational assistance for video editing tasks including:
    - Understanding user editing requests
    - Creating detailed editing plans
    - Providing direct editing instructions
    - Analyzing media content
    - Generating new media assets
    - Fetching stock footage
    
    **Authentication Required**: Bearer token (JWT)
    
    **Workflow:**
    1. User sends message with context (composition, media library, duration)
    2. Agent responds with appropriate action type
    3. Frontend processes action based on type
    

    **Response Types:**
    - `info`: Informational response, workflow continues automatically
    - `chat`: Conversational interaction requiring user input, workflow pauses
    - `edit`: Direct editing instructions for composition changes
    - `probe`: Media content analysis requests
    - `generate`: Media generation requests (images or videos)
    - `fetch`: Stock video search and selection requests
    **Context Fields:**
    - `messages`: Full conversation history (chronological)
    - `currentComposition`: Current timeline blueprint (tracks and clips)
    - `mediaLibrary`: Available media files with metadata
    - `compositionDuration`: Total composition length in seconds
    
    **Example Request:**
    ```json
    {
      "messages": [
        {
          "id": "msg-1",
          "content": "Add a title that says Welcome",
          "isUser": true,
          "timestamp": "2025-10-11T10:30:00Z"
        }
      ],
      "currentComposition": [...],
      "mediaLibrary": [...],
      "compositionDuration": 30.0
    }
    ```
    
    **Example Response (Chat - Plan):**
    ```json
    {
      "type": "chat",
      "content": "I'll add a 'Welcome' title at the beginning. The text will fade in at 0 seconds and stay visible until 3 seconds with large white text. Does this sound good? Say 'yes' to proceed.",
      "metadata": {
        "total_tokens": 1250,
        "model_used": "gemini-2.0-flash-exp"
      }
    }
    ```
    
    **Example Response (Edit - Execution):**
    ```json
    {
      "type": "edit",
      "content": "Add a text clip with 'Welcome' starting at 0 seconds, ending at 3 seconds. Apply a fade-in transition from 0 to 0.5 seconds. Style the text with large bold font, white color, and center alignment.",
      "metadata": {
        "total_tokens": 1480
      }
    }
    ```
    
    **Example Response (Probe):**
    ```json
    {
      "type": "probe",
      "content": "Let me analyze the background video to choose the right text color.",
      "fileName": "background.mp4",
      "question": "What are the dominant colors in this video?",
      "metadata": {
        "total_tokens": 950
      }
    }
    ```
    
    **Example Response (Generate):**
    ```json
    {
      "type": "generate",
      "content_type": "image",
      "content": "I'll create a sunset background image for you.",
      "prompt": "A dramatic golden hour sunset over mountain peaks with warm orange and purple sky tones",
      "suggestedName": "sunset_mountain_landscape",
      "metadata": {
        "total_tokens": 1100
      }
    }
    ```
    """
    # Extract user info from JWT
    user_id = user.get("user_id")
    session_id = user.get("session_id")
    
    if not user_id or not session_id:
        logger.error("Invalid JWT: missing user_id or session_id")
        raise HTTPException(
            status_code=400,
            detail="Invalid JWT: missing user_id or session_id"
        )
    
    logger.info(f"Agent chat request from user={user_id}, session={session_id}")
    
    try:
        import json
        from datetime import datetime
        from pathlib import Path
        
        # Validate we have messages
        if not request.messages or len(request.messages) == 0:
            raise HTTPException(
                status_code=400,
                detail="No messages provided in conversation"
            )
        
        # Build conversation history for context
        # Include ALL messages - the workflow needs complete history including analysis results
        conversation_history = [
            {
                "role": "user" if msg.isUser else "assistant",
                "content": msg.content
            }
            for msg in request.messages
        ]
        
        logger.info(f"📥 Received {len(request.messages)} messages, built history with {len(conversation_history)} entries")
        
        # Convert composition to JSON string
        composition_json = None
        if request.currentComposition:
            composition_json = json.dumps(request.currentComposition, indent=2)
        
        # Extract media library with URLs (not just names)
        # AI needs URLs to create probe requests with actual file locations
        logger.info(f"📥 Raw mediaLibrary from frontend: {len(request.mediaLibrary) if request.mediaLibrary else 0} items")
        
        media_library = None
        if request.mediaLibrary:
            media_library = [
                {
                    "name": media.get("name"),
                    "url": media.get("gcsUri") or media.get("mediaUrlRemote"),  # Prefer gs:// URI for Vertex AI
                    "type": media.get("mediaType")
                }
                for media in request.mediaLibrary 
                if media.get("name") and (media.get("gcsUri") or media.get("mediaUrlRemote"))
            ]
            logger.info(f"📚 Processed media library for AI agent: {len(media_library)} items (filtered from {len(request.mediaLibrary)})")
            for item in media_library:
                logger.info(f"  - {item['name']}: {item['url'][:80]}...")
        
        # Call agent service (no user_message - it's in conversation_history)
        # Exact messages sent to AI are now logged in invoke_agent.py as ai_request_{session_id}_{timestamp}.json
        result = await service.chat(
            conversation_history=conversation_history,
            composition_json=composition_json,
            media_library=media_library,
            duration=request.compositionDuration,
            user_id=user_id,
            session_id=session_id
        )
        
        # Convert to response model
        return AgentResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in agent_chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/capabilities")
async def get_agent_capabilities(
    service: AgentService = Depends(get_agent_service)
) -> Dict:
    """
    Get agent capabilities and available action types.
    
    Returns information about what the agent can do and how to use it.
    
    **Authentication**: Not required (public endpoint)
    
    **Returns:**
    ```json
    {
      "action_types": {
        "chat": "Description...",
        "sleep": "Description...",
        ...
      },
      "features": ["feature1", "feature2", ...],
      "workflow_steps": ["step1", "step2", ...]
    }
    ```
    """
    try:
        capabilities = await service.get_capabilities()
        return capabilities
    except Exception as e:
        logger.error(f"Error getting agent capabilities: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agent capabilities: {str(e)}"
        )
