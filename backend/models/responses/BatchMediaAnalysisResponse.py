"""
Batch Media Analysis Response Models.

Pydantic models for batch media analysis API responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class VideoAnalysisResult(BaseModel):
    """Result for a single video in a batch analysis."""
    
    file_url: str = Field(
        ...,
        description="The URL of the analyzed video"
    )
    
    title: Optional[str] = Field(
        None,
        description="Title/name of the video"
    )
    
    success: bool = Field(
        ...,
        description="Whether analysis succeeded for this video"
    )
    
    analysis: Optional[str] = Field(
        None,
        description="The AI-generated analysis"
    )
    
    error_message: Optional[str] = Field(
        None,
        description="Error message if analysis failed"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Token usage and other metadata"
    )


class BatchMediaAnalysisResponse(BaseModel):
    """Response model for batch media analysis endpoint."""
    
    success: bool = Field(
        ...,
        description="Whether the batch analysis completed (even if some videos failed)"
    )
    
    aggregated_analysis: str = Field(
        ...,
        description="Single aggregated text with all video analyses formatted as: 'Video 1 (Title): analysis...'"
    )
    
    results: List[VideoAnalysisResult] = Field(
        ...,
        description="Per-video analysis results"
    )
    
    model_used: str = Field(
        ...,
        description="The AI model used for analysis"
    )
    
    question: str = Field(
        ...,
        description="The question that was asked about each video"
    )
    
    total_videos: int = Field(
        ...,
        description="Total number of videos processed"
    )
    
    successful_count: int = Field(
        ...,
        description="Number of videos successfully analyzed"
    )
    
    failed_count: int = Field(
        ...,
        description="Number of videos that failed analysis"
    )
    
    total_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Aggregated metadata (total tokens, duration, etc.)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "aggregated_analysis": "Video 1 (Surfing Adventure): The video shows surfers...\n\nVideo 2 (Product Demo): The video demonstrates...\n\nVideo 3 (Customer Interview): The video features...",
                "results": [
                    {
                        "file_url": "gs://my-bucket/videos/clip1.mp4",
                        "title": "Surfing Adventure",
                        "success": True,
                        "analysis": "The video shows surfers...",
                        "error_message": None,
                        "metadata": {"total_tokens": 4809}
                    }
                ],
                "model_used": "gemini-2.0-flash-exp",
                "question": "What activities are shown?",
                "total_videos": 3,
                "successful_count": 3,
                "failed_count": 0,
                "total_metadata": {
                    "total_tokens": 14427,
                    "duration_seconds": 8.5
                }
            }
        }
