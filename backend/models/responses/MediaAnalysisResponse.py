"""
Media Analysis Response Models.

Pydantic models for media analysis API responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class MediaAnalysisResponse(BaseModel):
    """Response model for media analysis endpoint."""
    
    success: bool = Field(
        ...,
        description="Whether the analysis was successful"
    )
    
    analysis: Optional[str] = Field(
        None,
        description="The AI-generated analysis of the media content"
    )
    
    model_used: str = Field(
        ...,
        description="The AI model used for analysis"
    )
    
    file_url: str = Field(
        ...,
        description="The URL of the analyzed media file"
    )
    
    question: str = Field(
        ...,
        description="The question that was asked about the media"
    )
    
    error_message: Optional[str] = Field(
        None,
        description="Error message if the analysis failed"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata (token usage, etc.)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "analysis": "The video shows surfers riding waves in the ocean...",
                "model_used": "gemini-2.0-flash-exp",
                "file_url": "gs://my-bucket/videos/surfing.mp4",
                "question": "What activities are shown in this video?",
                "error_message": None,
                "metadata": {
                    "prompt_tokens": 4657,
                    "response_tokens": 152,
                    "total_tokens": 4809
                }
            }
        }
