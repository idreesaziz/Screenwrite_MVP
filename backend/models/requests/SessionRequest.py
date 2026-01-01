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
    composition: Optional[Any] = Field(
        default=None,
        description="Current composition blueprint for title context"
    )
    media_bin: Optional[List[Any]] = Field(
        default=None,
        description="Current media bin items for title context"
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


class TextProperties(BaseModel):
    """Text element properties."""
    textContent: str = Field(description="Text content")
    fontSize: int = Field(default=48, description="Font size")
    fontFamily: str = Field(default="Arial", description="Font family")
    color: str = Field(default="#ffffff", description="Text color")
    textAlign: str = Field(default="center", description="Text alignment")
    fontWeight: str = Field(default="normal", description="Font weight")


class MediaBinItemSnapshot(BaseModel):
    """Media bin item for storage (without signed URLs)."""
    id: str = Field(description="Unique item ID")
    name: str = Field(description="Display name")
    mediaType: str = Field(description="Type: video, image, audio, text, element")
    gcs_path: Optional[str] = Field(default=None, description="GCS blob path for file lookup")
    media_width: int = Field(default=0, description="Width in pixels")
    media_height: int = Field(default=0, description="Height in pixels")
    durationInSeconds: float = Field(default=0, description="Duration for video/audio")
    text: Optional[TextProperties] = Field(default=None, description="Text properties if mediaType is text")


class SaveStateRequest(BaseModel):
    """Request to save session state (messages, composition, and media bin)."""
    messages: List[ChatMessage] = Field(description="Chat messages array")
    composition: Optional[Any] = Field(
        default=None, 
        description="Composition blueprint"
    )
    media_bin: Optional[List[MediaBinItemSnapshot]] = Field(
        default=None,
        description="Media bin items snapshot"
    )
