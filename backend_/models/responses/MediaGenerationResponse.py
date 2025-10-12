"""Response models for media generation endpoints."""

from pydantic import BaseModel, Field
from typing import Optional, Literal


class GeneratedAsset(BaseModel):
    """Metadata for a generated asset."""
    
    asset_id: str = Field(description="Unique asset identifier")
    content_type: Literal["image", "video"] = Field(description="Type of generated content")
    file_path: str = Field(description="Storage path (user_id/session_id/filename)")
    file_url: str = Field(description="Public URL to access the file")
    prompt: str = Field(description="Generation prompt used")
    width: int = Field(description="Asset width in pixels")
    height: int = Field(description="Asset height in pixels")
    duration_seconds: Optional[float] = Field(default=None, description="Video duration (video only)")
    file_size: int = Field(description="File size in bytes")


class MediaGenerationResponse(BaseModel):
    """Response from media generation endpoint."""
    
    success: bool = Field(description="Whether generation was successful")
    
    status: Literal["completed", "processing", "failed"] = Field(
        description="Generation status"
    )
    
    generated_asset: Optional[GeneratedAsset] = Field(
        default=None,
        description="Generated asset details (if completed)"
    )
    
    operation_id: Optional[str] = Field(
        default=None,
        description="Operation ID for async video generation"
    )
    
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if generation failed"
    )


class VideoStatusResponse(BaseModel):
    """Response from video status check endpoint."""
    
    success: bool = Field(description="Whether status check was successful")
    
    status: Literal["completed", "processing", "failed"] = Field(
        description="Current generation status"
    )
    
    generated_asset: Optional[GeneratedAsset] = Field(
        default=None,
        description="Generated asset if completed"
    )
    
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if failed"
    )
