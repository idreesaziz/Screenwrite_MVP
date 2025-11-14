"""Request model for media upload."""

from pydantic import BaseModel, Field
from typing import Optional


class MediaUploadResponse(BaseModel):
    """Response from media upload endpoint."""
    
    success: bool = Field(description="Whether upload was successful")
    name: str = Field(description="Short unique name for display and AI reference")
    file_path: str = Field(description="Storage path (user_id/session_id/filename)")
    file_url: str = Field(description="Public URL to access the file")
    gcs_uri: str = Field(description="GCS URI for Vertex AI access (gs://bucket/path)")
    signed_url: Optional[str] = Field(None, description="Signed URL with expiration")
    file_size: int = Field(description="File size in bytes")
    content_type: Optional[str] = Field(None, description="File MIME type")
    filename: Optional[str] = Field(None, description="Sanitized filename (safe for storage)")
    error_message: Optional[str] = Field(None, description="Error message if upload failed")
