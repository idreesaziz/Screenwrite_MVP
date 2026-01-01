"""
Chat Session Response Models.

Response schemas for session management endpoints.
"""

from typing import Optional, List, Any
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class ChatMessage(BaseModel):
    """Single chat message."""
    role: str
    content: str
    timestamp: Optional[str] = None


class SessionResponse(BaseModel):
    """Single session response."""
    id: UUID = Field(description="Session ID")
    user_id: UUID = Field(description="User ID")
    title: str = Field(description="Session title")
    messages: List[ChatMessage] = Field(default=[], description="Chat messages")
    composition: Any = Field(default=[], description="Composition blueprint")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class SessionListItem(BaseModel):
    """Session list item (without full messages/composition)."""
    id: UUID = Field(description="Session ID")
    title: str = Field(description="Session title")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class SessionListResponse(BaseModel):
    """List of sessions response."""
    sessions: List[SessionListItem] = Field(description="List of sessions")
    total: int = Field(description="Total count")


class SessionCreatedResponse(BaseModel):
    """Response after creating a session."""
    id: UUID = Field(description="Session ID")
    title: str = Field(description="Generated or default title")
    created_at: datetime = Field(description="Creation timestamp")
