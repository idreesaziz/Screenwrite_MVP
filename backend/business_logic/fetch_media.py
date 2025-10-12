"""
Business logic for stock media search and curation.

This service orchestrates the stock media workflow:
1. Searches for media using MediaProvider (Pexels, Shutterstock, etc.)
2. Curates results using AI (selects most relevant items)
3. Uploads selected items to cloud storage via StorageProvider
4. Returns storage URLs for frontend use
"""

import logging
from dataclasses import dataclass
from typing import Optional, Dict, List, Any
import uuid

from services.base.MediaProvider import (
    MediaProvider,
    MediaSearchRequest,
    MediaType,
    VideoOrientation
)
from services.base.StorageProvider import StorageProvider


logger = logging.getLogger(__name__)


@dataclass
class StockMediaResult:
    """Result from stock media search and curation"""
    success: bool
    query: str
    media_type: str
    items: List[Dict[str, Any]]  # List of curated media items
    total_results: int
    ai_curation_explanation: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict] = None


class StockMediaService:
    """
    Service for searching and curating stock media using AI.
    
    Uses MediaProvider base class for swappable media sources (Pexels, Shutterstock, etc.)
    and StorageProvider base class for swappable storage (GCS, S3, etc.)
    """
    
    def __init__(
        self,
        media_provider: MediaProvider,
        storage_provider: StorageProvider
    ):
        """
        Initialize with injected providers for dependency injection.
        
        Args:
            media_provider: Media search provider (e.g., PexelsMediaProvider)
            storage_provider: Cloud storage provider (e.g., GCStorageProvider)
        """
        self.media_provider = media_provider
        self.storage_provider = storage_provider
    
    async def search_stock_media(
        self,
        query: str,
        media_type: str,
        user_id: str,
        session_id: str,
        orientation: Optional[str] = "landscape",
        max_results: int = 4,
        per_page: int = 50
    ) -> StockMediaResult:
        """
        Search for stock media with AI curation and cloud storage upload.
        
        Workflow:
        1. Search media provider for results (e.g., Pexels)
        2. Use AI to curate and select most relevant items
        3. Upload selected items to cloud storage (user/session isolated)
        4. Return storage URLs for frontend use
        
        Args:
            query: Search query
            media_type: 'video' or 'image'
            user_id: User identifier for storage isolation
            session_id: Session identifier for storage isolation
            orientation: Media orientation ('landscape', 'portrait', 'square')
            max_results: Maximum curated results to return (1-10)
            per_page: Number of results to fetch for AI curation (10-80)
        
        Returns:
            StockMediaResult with curated items and storage URLs
        """
        try:
            logger.info(
                f"Searching stock {media_type} for user {user_id}, "
                f"session {session_id}: '{query}'"
            )
            
            # Convert media_type string to enum
            media_type_enum = MediaType.VIDEO if media_type == "video" else MediaType.IMAGE
            
            # Convert orientation string to enum
            orientation_enum = None
            if orientation:
                orientation_map = {
                    "landscape": VideoOrientation.LANDSCAPE,
                    "portrait": VideoOrientation.PORTRAIT,
                    "square": VideoOrientation.SQUARE
                }
                orientation_enum = orientation_map.get(orientation.lower())
            
            # Step 1: Search and curate with AI (combined operation)
            logger.info(f"Searching and curating {media_type} with AI...")
            search_request = MediaSearchRequest(
                query=query,
                media_type=media_type_enum,
                orientation=orientation_enum,
                per_page=per_page,
                page=1
            )
            
            curated_response = await self.media_provider.search_and_curate(
                request=search_request,
                max_curated=max_results
            )
            
            if not curated_response.curated_items:
                logger.warning(f"No relevant {media_type} found for query: '{query}'")
                return StockMediaResult(
                    success=True,
                    query=query,
                    media_type=media_type,
                    items=[],
                    total_results=curated_response.total_results,
                    ai_curation_explanation=curated_response.ai_curation_explanation or "No relevant results found"
                )
            
            logger.info(
                f"AI selected {len(curated_response.curated_items)} items from "
                f"{curated_response.total_results} results: "
                f"{curated_response.ai_curation_explanation}"
            )
            
            # Step 2: Upload selected items to cloud storage
            uploaded_items = []
            for idx, curated_item in enumerate(curated_response.curated_items):
                media_item = curated_item.media_item
                
                try:
                    # Determine download URL
                    if media_type == "video":
                        # Select best video file
                        download_url = await self._get_best_video_url(media_item)
                    else:
                        # Use image download URL
                        download_url = media_item.download_url or media_item.preview_url
                    
                    if not download_url:
                        logger.warning(f"No download URL for item {media_item.id}")
                        continue
                    
                    # Generate storage path
                    file_ext = ".mp4" if media_type == "video" else ".jpg"
                    file_name = f"stock_{media_type}_{uuid.uuid4()}{file_ext}"
                    
                    # Upload to storage (user/session isolated)
                    logger.info(f"Uploading {media_type} {idx+1}/{len(curated_response.curated_items)}")
                    upload_result = await self.storage_provider.upload_from_url(
                        url=download_url,
                        user_id=user_id,
                        session_id=session_id,
                        filename=file_name
                    )
                    storage_url = upload_result.url
                    
                    # Build response item
                    uploaded_items.append({
                        "id": media_item.id,
                        "media_type": media_type,
                        "storage_url": storage_url,
                        "preview_url": media_item.preview_url,
                        "provider_url": media_item.url,
                        "width": media_item.width,
                        "height": media_item.height,
                        "duration": media_item.duration if media_type == "video" else None,
                        "creator_name": media_item.creator.name if media_item.creator else None,
                        "creator_url": media_item.creator.url if media_item.creator else None,
                        "quality": self._get_quality(media_item),
                        "avg_color": media_item.avg_color
                    })
                    
                    logger.info(f"✅ Uploaded {file_name} → {storage_url}")
                    
                except Exception as e:
                    logger.error(f"Failed to upload item {media_item.id}: {e}")
                    continue
            
            if not uploaded_items:
                return StockMediaResult(
                    success=False,
                    query=query,
                    media_type=media_type,
                    items=[],
                    total_results=curated_response.total_results,
                    error_message="Failed to upload any selected items"
                )
            
            logger.info(
                f"✅ Successfully processed {len(uploaded_items)} "
                f"{media_type} items for '{query}'"
            )
            
            return StockMediaResult(
                success=True,
                query=query,
                media_type=media_type,
                items=uploaded_items,
                total_results=curated_response.total_results,
                ai_curation_explanation=curated_response.ai_curation_explanation,
                metadata={
                    "provider": self.media_provider.__class__.__name__,
                    "storage": self.storage_provider.__class__.__name__
                }
            )
            
        except Exception as e:
            logger.error(f"Stock media search failed: {str(e)}", exc_info=True)
            return StockMediaResult(
                success=False,
                query=query,
                media_type=media_type,
                items=[],
                total_results=0,
                error_message=str(e)
            )
    
    async def _get_best_video_url(self, media_item) -> Optional[str]:
        """Get the best quality video URL from media item."""
        if not media_item.video_files:
            return None
        
        # Prefer HD MP4
        hd_mp4 = [vf for vf in media_item.video_files 
                  if vf.quality == "hd" and vf.file_type == "video/mp4"]
        if hd_mp4:
            # Prefer 1920x1080 or 1280x720
            preferred = [vf for vf in hd_mp4 if vf.width in [1920, 1280]]
            return (preferred[0] if preferred else hd_mp4[0]).link
        
        # Fallback to SD MP4
        sd_mp4 = [vf for vf in media_item.video_files 
                  if vf.quality == "sd" and vf.file_type == "video/mp4"]
        if sd_mp4:
            return sd_mp4[0].link
        
        # Last resort: any video file
        return media_item.video_files[0].link if media_item.video_files else None
    
    def _get_quality(self, media_item) -> Optional[str]:
        """Extract quality from media item."""
        if media_item.video_files:
            # Return quality of best file
            for vf in media_item.video_files:
                if vf.quality:
                    return vf.quality
        return None
