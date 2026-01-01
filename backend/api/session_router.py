"""
Session API Router.

Handles endpoints for chat session management.
"""

import logging
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query

from models.requests.SessionRequest import CreateSessionRequest, UpdateSessionRequest, SaveStateRequest
from models.responses.SessionResponse import (
    SessionResponse,
    SessionListResponse,
    SessionListItem,
    SessionCreatedResponse,
    ChatMessage
)
from business_logic.session_service import SessionService
from core.dependencies import get_session_service
from core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Sessions"])


@router.post("", response_model=SessionCreatedResponse)
async def create_session(
    request: CreateSessionRequest,
    user: dict = Depends(get_current_user),
    service: SessionService = Depends(get_session_service)
) -> SessionCreatedResponse:
    """
    Create a new chat session.
    
    The session_id should match the GCS prefix for media storage.
    If first_message is provided, a title will be auto-generated.
    """
    user_id = user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid user")
    
    try:
        session = await service.create_session(
            user_id=UUID(user_id),
            session_id=request.session_id,
            first_message=request.first_message
        )
        
        return SessionCreatedResponse(
            id=UUID(session["id"]),
            title=session["title"],
            created_at=session["created_at"]
        )
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: dict = Depends(get_current_user),
    service: SessionService = Depends(get_session_service)
) -> SessionListResponse:
    """
    List user's chat sessions, sorted by most recent.
    """
    user_id = user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid user")
    
    try:
        sessions, total = await service.list_sessions(
            user_id=UUID(user_id),
            limit=limit,
            offset=offset
        )
        
        return SessionListResponse(
            sessions=[
                SessionListItem(
                    id=UUID(s["id"]),
                    title=s["title"],
                    created_at=s["created_at"],
                    updated_at=s["updated_at"]
                )
                for s in sessions
            ],
            total=total
        )
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    user: dict = Depends(get_current_user),
    service: SessionService = Depends(get_session_service)
) -> SessionResponse:
    """
    Get a single session with full data (messages, composition).
    """
    user_id = user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid user")
    
    try:
        session = await service.get_session(
            user_id=UUID(user_id),
            session_id=session_id
        )
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionResponse(
            id=UUID(session["id"]),
            user_id=UUID(session["user_id"]),
            title=session["title"],
            messages=[
                ChatMessage(**m) for m in (session.get("messages") or [])
            ],
            composition=session.get("composition") or [],
            created_at=session["created_at"],
            updated_at=session["updated_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: UUID,
    request: UpdateSessionRequest,
    user: dict = Depends(get_current_user),
    service: SessionService = Depends(get_session_service)
) -> SessionResponse:
    """
    Update a session's title, messages, or composition.
    """
    user_id = user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid user")
    
    try:
        # Convert messages to dict format
        messages_data = None
        if request.messages is not None:
            messages_data = [m.model_dump() for m in request.messages]
        
        session = await service.update_session(
            user_id=UUID(user_id),
            session_id=session_id,
            title=request.title,
            messages=messages_data,
            composition=request.composition
        )
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionResponse(
            id=UUID(session["id"]),
            user_id=UUID(session["user_id"]),
            title=session["title"],
            messages=[
                ChatMessage(**m) for m in (session.get("messages") or [])
            ],
            composition=session.get("composition") or [],
            created_at=session["created_at"],
            updated_at=session["updated_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/state", response_model=SessionResponse)
async def save_session_state(
    session_id: UUID,
    request: SaveStateRequest,
    user: dict = Depends(get_current_user),
    service: SessionService = Depends(get_session_service)
) -> SessionResponse:
    """
    Save session state (messages and composition).
    This is the primary endpoint for auto-saving chat progress.
    """
    user_id = user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid user")
    
    try:
        session = await service.save_state(
            user_id=UUID(user_id),
            session_id=session_id,
            messages=[m.model_dump() for m in request.messages],
            composition=request.composition
        )
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionResponse(
            id=UUID(session["id"]),
            user_id=UUID(session["user_id"]),
            title=session["title"],
            messages=[
                ChatMessage(**m) for m in (session.get("messages") or [])
            ],
            composition=session.get("composition") or [],
            created_at=session["created_at"],
            updated_at=session["updated_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save session state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}")
async def delete_session(
    session_id: UUID,
    user: dict = Depends(get_current_user),
    service: SessionService = Depends(get_session_service)
):
    """
    Delete a session.
    
    Note: This does NOT delete media files from GCS.
    Call the media cleanup endpoint separately if needed.
    """
    user_id = user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid user")
    
    try:
        deleted = await service.delete_session(
            user_id=UUID(user_id),
            session_id=session_id
        )
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"status": "deleted", "session_id": str(session_id)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete session: {e}")
        raise HTTPException(status_code=500, detail=str(e))
