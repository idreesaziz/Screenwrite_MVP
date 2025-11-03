"""
Abstract base class for media search providers.

This module defines the contract that all media provider implementations must follow.
It provides a consistent interface for different stock media services (Pexels, Unsplash, Pixabay, etc.).
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class MediaType(Enum):
    """Types of media that can be searched"""
    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"


class VideoOrientation(Enum):
    """Video orientation options"""
    LANDSCAPE = "landscape"
    PORTRAIT = "portrait"
    SQUARE = "square"


@dataclass
class MediaSearchRequest:
    """
    Represents a request to search for media.
    
    Attributes:
        query: Search query string
        media_type: Type of media to search for (video, image, audio)
        per_page: Number of results per page
        page: Page number for pagination
        orientation: Video/image orientation filter
        size: Size filter (e.g., "large", "medium", "small")
        min_duration: Minimum duration in seconds (for videos)
        max_duration: Maximum duration in seconds (for videos)
        min_width: Minimum width in pixels
        min_height: Minimum height in pixels
        locale: Locale for search results
        metadata: Optional additional search parameters
    """
    query: str
    media_type: MediaType = MediaType.VIDEO
    per_page: int = 15
    page: int = 1
    orientation: Optional[VideoOrientation] = None
    size: Optional[str] = None
    min_duration: Optional[int] = None
    max_duration: Optional[int] = None
    min_width: Optional[int] = None
    min_height: Optional[int] = None
    locale: Optional[str] = "en-US"
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class VideoFile:
    """
    Represents a single video file variant.
    
    Attributes:
        id: Unique identifier for this video file
        quality: Quality level (e.g., "hd", "sd", "4k")
        file_type: MIME type (e.g., "video/mp4")
        width: Video width in pixels
        height: Video height in pixels
        fps: Frames per second
        link: Direct download URL
        size_bytes: File size in bytes (if available)
    """
    id: int
    quality: str
    file_type: str
    width: int
    height: int
    fps: Optional[float] = None
    link: str = ""
    size_bytes: Optional[int] = None


@dataclass
class MediaCreator:
    """
    Represents the creator of a media item.
    
    Attributes:
        id: Creator's unique ID on the platform
        name: Creator's display name
        url: Link to creator's profile
    """
    id: int
    name: str
    url: str


@dataclass
class MediaItem:
    """
    Represents a single media item (video, image, etc.).
    
    Attributes:
        id: Unique identifier from the provider
        media_type: Type of media (video, image, audio)
        url: URL to the media page on provider's website
        width: Media width in pixels
        height: Media height in pixels
        duration: Duration in seconds (for videos/audio)
        preview_url: URL to preview image/thumbnail
        creator: Information about the media creator
        video_files: List of available video file variants (for videos)
        download_url: Direct download URL (for images)
        alt_text: Alternative text description
        avg_color: Average color of the media (hex code)
        metadata: Additional provider-specific metadata
    """
    id: int
    media_type: MediaType
    url: str
    width: int
    height: int
    duration: Optional[int] = None
    preview_url: Optional[str] = None
    creator: Optional[MediaCreator] = None
    video_files: Optional[List[VideoFile]] = None
    download_url: Optional[str] = None
    alt_text: Optional[str] = None
    avg_color: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class CuratedMediaItem:
    """
    Represents a media item that has been curated/ranked by AI.
    
    Attributes:
        media_item: The original media item
        relevance_score: AI-assigned relevance score (0-100)
        relevance_reasoning: Explanation of why this item was selected
        gcs_uri: Google Cloud Storage URI (if uploaded)
        gcs_public_url: Public URL for the uploaded media
        local_path: Local file path (if downloaded)
        file_size_bytes: Size of the downloaded file
    """
    media_item: MediaItem
    relevance_score: Optional[float] = None
    relevance_reasoning: Optional[str] = None
    gcs_uri: Optional[str] = None
    gcs_public_url: Optional[str] = None
    local_path: Optional[str] = None
    file_size_bytes: Optional[int] = None


@dataclass
class MediaSearchResponse:
    """
    Represents a response from a media search.
    
    Attributes:
        query: Original search query
        media_items: List of media items found
        curated_items: AI-curated subset of media items (if curation was performed)
        total_results: Total number of results available
        page: Current page number
        per_page: Results per page
        ai_curation_explanation: Explanation from AI about curation choices
        provider: Name of the media provider (e.g., "pexels")
        metadata: Additional response metadata
        timestamp: When the search was performed
    """
    query: str
    media_items: List[MediaItem]
    curated_items: Optional[List[CuratedMediaItem]] = None
    total_results: int = 0
    page: int = 1
    per_page: int = 15
    ai_curation_explanation: Optional[str] = None
    provider: str = "unknown"
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MediaDownloadRequest:
    """
    Represents a request to download and optionally upload media.
    
    Attributes:
        media_item: The media item to download
        quality_preference: Preferred quality ("best", "hd", "sd", "lowest")
        upload_to_gcs: Whether to upload to Google Cloud Storage
        gcs_bucket: GCS bucket name (if uploading)
        gcs_path: GCS path within bucket (if uploading)
        local_path: Local path to save file (if not uploading to GCS)
    """
    media_item: MediaItem
    quality_preference: str = "hd"
    upload_to_gcs: bool = True
    gcs_bucket: Optional[str] = None
    gcs_path: Optional[str] = None
    local_path: Optional[str] = None


class MediaProvider(ABC):
    """
    Abstract base class for media search providers.
    
    All media provider implementations (Pexels, Unsplash, etc.) must implement
    these methods to provide a consistent interface across different stock media services.
    """
    
    @abstractmethod
    async def search_media(
        self,
        request: MediaSearchRequest,
        **kwargs
    ) -> MediaSearchResponse:
        """
        Search for media items.
        
        Args:
            request: MediaSearchRequest with search parameters
            **kwargs: Provider-specific parameters
            
        Returns:
            MediaSearchResponse with found media items
            
        Raises:
            ValueError: If request parameters are invalid
            RuntimeError: If API call fails
        """
        pass
    
    @abstractmethod
    async def search_and_curate(
        self,
        request: MediaSearchRequest,
        max_curated: int = 3,
        **kwargs
    ) -> MediaSearchResponse:
        """
        Search for media and use AI to curate the most relevant results.
        
        This method searches for media items and uses an LLM to select the most
        relevant ones based on the query context.
        
        Args:
            request: MediaSearchRequest with search parameters
            max_curated: Maximum number of items to curate (0-N)
            **kwargs: Provider-specific parameters
            
        Returns:
            MediaSearchResponse with curated media items
            
        Raises:
            ValueError: If request parameters are invalid
            RuntimeError: If search or curation fails
        """
        pass
    
    @abstractmethod
    async def download_media(
        self,
        request: MediaDownloadRequest,
        **kwargs
    ) -> CuratedMediaItem:
        """
        Download a media item and optionally upload to cloud storage.
        
        Args:
            request: MediaDownloadRequest with download/upload parameters
            **kwargs: Provider-specific parameters
            
        Returns:
            CuratedMediaItem with download/upload information
            
        Raises:
            ValueError: If request parameters are invalid
            RuntimeError: If download or upload fails
        """
        pass
    
    @abstractmethod
    async def get_media_details(
        self,
        media_id: str,
        media_type: MediaType,
        **kwargs
    ) -> MediaItem:
        """
        Get detailed information about a specific media item.
        
        Args:
            media_id: Unique identifier for the media item
            media_type: Type of media (video, image, audio)
            **kwargs: Provider-specific parameters
            
        Returns:
            MediaItem with detailed information
            
        Raises:
            ValueError: If media_id is invalid
            RuntimeError: If API call fails or media not found
        """
        pass
