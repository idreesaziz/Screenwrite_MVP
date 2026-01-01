"""
Chat Session Request Models.

Request schemas for session management endpoints.
"""

from typing import Optional, List, Any
from pydantic import BaseModel, Field
from uuid import UUID


class ChatMessage(BaseModel):
    """Single chat message."""
    role: str = Field(description="Message role: user, assistant, system, tool")
    content: str = Field(description="Message content")
    timestamp: Optional[str] = Field(default=None, description="ISO timestamp")


class CreateSessionRequest(BaseModel):
    """Request to create a new chat session."""
    session_id: Optional[UUID] = Field(
        default=None, 
        description="Session ID (matches GCS prefix). Auto-generated if not provided."
    )
    first_message: Optional[str] = Field(
        default=None, 
        description="First user message for title generation"
    )


class UpdateSessionRequest(BaseModel):
    """Request to update a chat session."""
    title: Optional[str] = Field(default=None, description="New session title")
    messages: Optional[List[ChatMessage]] = Field(
        default=None, 
        description="Updated messages array"
    )
    composition: Optional[Any] = Field(
        default=None, 
        description="Updated composition blueprint"
    )


class SaveStateRequest(BaseModel):
    """Request to save session state (messages and composition)."""
    messages: List[ChatMessage] = Field(description="Chat messages array")
    composition: Optional[Any] = Field(
        default=None, 
        description="Composition blueprint"
    )
