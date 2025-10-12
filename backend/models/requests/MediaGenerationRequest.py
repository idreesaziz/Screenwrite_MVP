"""Request models for media generation endpoints."""

from pydantic import BaseModel, Field
from typing import Optional, Literal


class MediaGenerationRequest(BaseModel):
    """Request for generating image or video content."""
    
    content_type: Literal["image", "video"] = Field(
        description="Type of content to generate"
    )
    
    prompt: str = Field(
        description="Text description of content to generate",
        min_length=1,
        max_length=2000
    )
    
    negative_prompt: Optional[str] = Field(
        default=None,
        description="What to avoid in generation (video only)",
        max_length=500
    )
    
    aspect_ratio: str = Field(
        default="16:9",
        description="Content aspect ratio ('16:9', '9:16')"
    )
    
    resolution: str = Field(
        default="720p",
        description="Video resolution ('720p', '1080p'). Images are always high quality."
    )
    
    reference_image_url: Optional[str] = Field(
        default=None,
        description="Optional reference image URL for image-to-video generation"
    )


class VideoStatusRequest(BaseModel):
    """Request for checking video generation status."""
    
    operation_id: str = Field(
        description="Operation ID returned from video generation",
        min_length=1
    )
