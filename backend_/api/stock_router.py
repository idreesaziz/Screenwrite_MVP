"""
API router for stock media search endpoints.

Provides REST API for searching and curating stock media (videos/images)
from providers like Pexels with AI-powered curation.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict

from models.requests.StockMediaSearchRequest import StockMediaSearchRequest
from models.responses.StockMediaSearchResponse import (
    StockMediaSearchResponse,
    StockMediaItem
)
from business_logic.fetch_media import StockMediaService
from core.security import get_current_user
from core.dependencies import get_stock_media_service


logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/search",
    response_model=StockMediaSearchResponse,
    summary="Search for stock media with AI curation",
    description="""
    Search for stock videos or images from providers like Pexels with intelligent AI curation.
    
    Workflow:
    1. Searches provider for results (up to 80 items)
    2. AI curates and selects most relevant items (0-10)
    3. Uploads selected items to cloud storage (user/session isolated)
    4. Returns storage URLs ready for use in compositions
    
    Features:
    - AI-powered relevance ranking
    - Automatic cloud storage upload
    - User/session isolation
    - Support for videos and images
    - Multiple orientation options
    """,
    responses={
        200: {
            "description": "Stock media search completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "query": "ocean waves",
                        "media_type": "video",
                        "items": [
                            {
                                "id": 123456,
                                "media_type": "video",
                                "storage_url": "https://storage.googleapis.com/.../stock_video_abc123.mp4",
                                "preview_url": "https://images.pexels.com/videos/.../preview.jpg",
                                "provider_url": "https://www.pexels.com/video/ocean-waves-123456/",
                                "width": 1920,
                                "height": 1080,
                                "duration": 15.5,
                                "creator_name": "John Doe",
                                "creator_url": "https://www.pexels.com/@johndoe",
                                "quality": "hd",
                                "avg_color": "#3B7EA1"
                            }
                        ],
                        "total_results": 42,
                        "ai_curation_explanation": "Selected videos showing calm ocean waves with good composition",
                        "metadata": {
                            "provider": "PexelsMediaProvider",
                            "storage": "GCStorageProvider"
                        }
                    }
                }
            }
        },
        400: {"description": "Invalid request parameters"},
        401: {"description": "Unauthorized - invalid or missing JWT token"},
        500: {"description": "Internal server error during search"}
    }
)
async def search_stock_media(
    request: StockMediaSearchRequest,
    user: Dict = Depends(get_current_user),
    service: StockMediaService = Depends(get_stock_media_service)
) -> StockMediaSearchResponse:
    """
    Search for stock media with AI curation and automatic cloud storage.
    
    Requires JWT authentication. User and session information is extracted
    from the JWT token for storage isolation and tracking.
    """
    try:
        # Extract user info from JWT
        user_id = user.get("user_id")
        session_id = user.get("session_id")
        
        if not user_id or not session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JWT: missing user_id or session_id"
            )
        
        logger.info(
            f"Stock media search request from user {user_id}, "
            f"session {session_id}: '{request.query}' ({request.media_type})"
        )
        
        # Search and curate stock media
        result = await service.search_stock_media(
            query=request.query,
            media_type=request.media_type,
            user_id=user_id,
            session_id=session_id,
            orientation=request.orientation,
            max_results=request.max_results,
            per_page=request.per_page
        )
        
        # Convert result items to response models
        response_items = [
            StockMediaItem(**item) for item in result.items
        ]
        
        return StockMediaSearchResponse(
            success=result.success,
            query=result.query,
            media_type=result.media_type,
            items=response_items,
            total_results=result.total_results,
            ai_curation_explanation=result.ai_curation_explanation,
            error_message=result.error_message,
            metadata=result.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stock media search failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search stock media: {str(e)}"
        )


@router.get(
    "/health",
    summary="Health check for stock media service",
    description="Verify that the stock media search service is operational"
)
async def health_check() -> Dict[str, str]:
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "service": "stock_media"
    }
