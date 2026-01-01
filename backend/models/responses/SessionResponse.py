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


class TextProperties(BaseModel):
    """Text element properties."""
    textContent: str
    fontSize: int = 48
    fontFamily: str = "Arial"
    color: str = "#ffffff"
    textAlign: str = "center"
    fontWeight: str = "normal"


class MediaBinItemResponse(BaseModel):
    """Media bin item with refreshed signed URL."""
    id: str = Field(description="Unique item ID")
    name: str = Field(description="Display name")
    mediaType: str = Field(description="Type: video, image, audio, text, element")
    mediaUrlRemote: Optional[str] = Field(default=None, description="Signed URL for playback")
    gcsUri: Optional[str] = Field(default=None, description="GCS URI for backend reference")
    media_width: int = Field(default=0, description="Width in pixels")
    media_height: int = Field(default=0, description="Height in pixels")
    durationInSeconds: float = Field(default=0, description="Duration for video/audio")
    text: Optional[TextProperties] = Field(default=None, description="Text properties if mediaType is text")
    upload_status: str = Field(default="uploaded", description="Upload status")


class MissingFile(BaseModel):
    """Info about a file that was in the session but no longer exists in GCS."""
    id: str = Field(description="Item ID")
    name: str = Field(description="Item name")
    reason: str = Field(default="File not found in storage", description="Why it's missing")


class SessionResponse(BaseModel):
    """Single session response."""
    id: UUID = Field(description="Session ID")
    user_id: UUID = Field(description="User ID")
    title: str = Field(description="Session title")
    messages: List[ChatMessage] = Field(default=[], description="Chat messages")
    composition: Any = Field(default=[], description="Composition blueprint")
    media_bin: List[MediaBinItemResponse] = Field(default=[], description="Media bin items with refreshed URLs")
    missing_files: List[MissingFile] = Field(default=[], description="Files that no longer exist in GCS")
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
