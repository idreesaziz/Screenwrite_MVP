"""
Batch Media Analysis Request Models.

Pydantic models for batch media analysis API requests.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List


class VideoAnalysisItem(BaseModel):
    """Individual video to analyze in a batch request."""
    
    file_url: str = Field(
        ...,
        description="URL of the media file to analyze (GCS URI or HTTP/HTTPS URL)",
        examples=[
            "gs://my-bucket/videos/sample.mp4",
            "https://storage.googleapis.com/bucket/file.mp4?X-Goog-Signature=..."
        ]
    )
    
    title: Optional[str] = Field(
        None,
        description="Optional title/name for this video (used in aggregated output)",
        examples=["Holiday Clip", "Product Demo", "Interview"]
    )
    
    question: Optional[str] = Field(
        None,
        description="Optional per-video question. If not provided, falls back to global question field.",
        examples=[
            "What is happening in this video?",
            "Describe the main activities shown"
        ]
    )

    audio_timestamp: Optional[bool] = Field(
        None,
        description="Optional per-video override to request timestamps for audio-only files",
        examples=[True, False]
    )


class BatchMediaAnalysisRequest(BaseModel):
    """Request model for batch media analysis endpoint."""
    
    videos: List[VideoAnalysisItem] = Field(
        ...,
        description="List of videos to analyze (3-4 recommended for optimal performance)",
        min_length=1,
        max_length=10
    )
    
    question: Optional[str] = Field(
        None,
        description="Global question to ask about each video (optional if per-video questions are provided)",
        examples=[
            "What is happening in this video?",
            "Describe the main activities shown",
            "What objects are visible?"
        ],
        min_length=1,
        max_length=2000
    )
    
    model_name: Optional[str] = Field(
        None,
        description="Optional model override (e.g., 'gemini-2.5-flash', 'gemini-2.0-flash-exp')",
        examples=["gemini-2.5-flash", "gemini-2.0-flash-exp"]
    )
    
    temperature: float = Field(
        0.1,
        description="Generation temperature (0.0-1.0). Lower = more focused, Higher = more creative",
        ge=0.0,
        le=1.0
    )
    
    max_concurrent: int = Field(
        4,
        description="Maximum number of concurrent analysis requests (1-10)",
        ge=1,
        le=10
    )

    audio_timestamp: Optional[bool] = Field(
        None,
        description="Optional global toggle to request timestamps for audio-only files",
        examples=[True, False]
    )
    
    @field_validator('videos')
    @classmethod
    def check_video_count(cls, v):
        """Validate video count is reasonable."""
        if len(v) > 10:
            raise ValueError("Maximum 10 videos per batch request")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "videos": [
                    {
                        "file_url": "gs://my-bucket/videos/clip1.mp4",
                        "title": "Surfing Adventure"
                    },
                    {
                        "file_url": "gs://my-bucket/videos/clip2.mp4",
                        "title": "Product Demo"
                    },
                    {
                        "file_url": "gs://my-bucket/videos/clip3.mp4",
                        "title": "Customer Interview"
                    }
                ],
                "question": "What activities are shown in this video?",
                "temperature": 0.1,
                "max_concurrent": 4,
                "audio_timestamp": None
            }
        }
