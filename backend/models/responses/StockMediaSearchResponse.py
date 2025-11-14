from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class StockMediaItem(BaseModel):
    """A single stock media item with storage URL"""
    
    id: int = Field(description="Provider's media ID")
    
    name: str = Field(description="Short unique name for display and AI reference")
    
    media_type: str = Field(description="Type: 'video' or 'image'")
    
    storage_url: str = Field(description="URL to media in cloud storage (GCS, S3, etc.)")
    
    preview_url: str = Field(description="URL to preview image/thumbnail")
    
    provider_url: str = Field(description="Original URL on provider's website (Pexels, etc.)")
    
    width: int = Field(description="Media width in pixels")
    
    height: int = Field(description="Media height in pixels")
    
    duration: Optional[float] = Field(
        default=None,
        description="Duration in seconds (video only)"
    )
    
    creator_name: str = Field(description="Creator/photographer name")
    
    creator_url: str = Field(description="Link to creator's profile")
    
    file_size_bytes: Optional[int] = Field(
        default=None,
        description="File size in bytes"
    )
    
    quality: Optional[str] = Field(
        default=None,
        description="Quality level (e.g., 'hd', 'sd')"
    )
    
    avg_color: Optional[str] = Field(
        default=None,
        description="Average color (hex format)"
    )


class StockMediaSearchResponse(BaseModel):
    """Response from stock media search with AI curation"""
    
    success: bool = Field(description="Whether the search was successful")
    
    query: str = Field(description="Original search query")
    
    media_type: str = Field(description="Type of media searched: 'video' or 'image'")
    
    items: List[StockMediaItem] = Field(
        description="Curated stock media items with storage URLs"
    )
    
    total_results: int = Field(
        description="Total number of results found before AI curation"
    )
    
    ai_curation_explanation: Optional[str] = Field(
        default=None,
        description="AI explanation for why these items were selected"
    )
    
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if search failed"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata (processing time, provider info, etc.)"
    )
