from typing import Optional, List
from pydantic import BaseModel, Field


class StockMediaSearchRequest(BaseModel):
    """Request to search for stock media (videos or images)"""
    
    query: str = Field(
        description="Search query for stock media",
        examples=["ocean waves", "sunset", "business meeting"]
    )
    
    media_type: str = Field(
        default="video",
        description="Type of media to search for: 'video' or 'image'",
        pattern="^(video|image)$"
    )
    
    orientation: Optional[str] = Field(
        default="landscape",
        description="Media orientation: 'landscape', 'portrait', or 'square'",
        pattern="^(landscape|portrait|square)$"
    )
    
    max_results: int = Field(
        default=4,
        ge=1,
        le=10,
        description="Maximum number of curated results to return (1-10)"
    )
    
    per_page: int = Field(
        default=50,
        ge=10,
        le=80,
        description="Number of results to fetch for AI curation (10-80)"
    )
