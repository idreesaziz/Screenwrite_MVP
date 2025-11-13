"""
Media Analysis Request Models.

Pydantic models for media analysis API requests.
"""

from pydantic import BaseModel, Field
from typing import Optional


class MediaAnalysisRequest(BaseModel):
    """Request model for media analysis endpoint."""
    
    file_url: str = Field(
        ...,
        description="URL of the media file to analyze (GCS URI or HTTP/HTTPS URL)",
        examples=[
            "gs://my-bucket/videos/sample.mp4",
            "https://storage.googleapis.com/bucket/file.mp4?X-Goog-Signature=..."
        ]
    )
    
    question: str = Field(
        ...,
        description="Question to ask about the media content",
        examples=[
            "What is happening in this video?",
            "Describe the main activities shown",
            "What objects are visible in this image?"
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

    audio_timestamp: bool = Field(
        False,
        description="Set to true to request word-level timestamps for audio-only files",
        examples=[False, True]
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_url": "gs://my-bucket/videos/surfing.mp4",
                "question": "What activities are shown in this video?",
                "temperature": 0.1,
                "audio_timestamp": False
            }
        }
