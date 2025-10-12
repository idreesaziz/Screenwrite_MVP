"""
API router for AI-powered media generation endpoints.

Provides REST API for generating images and videos with Imagen and Veo.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status

from models.requests.MediaGenerationRequest import (
    MediaGenerationRequest,
    VideoStatusRequest
)
from models.responses.MediaGenerationResponse import (
    MediaGenerationResponse,
    VideoStatusResponse,
    GeneratedAsset
)
from business_logic.generate_media import MediaGenerationService
from core.security import get_current_user
from core.dependencies import get_media_generation_service


logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/generate",
    response_model=MediaGenerationResponse,
    summary="Generate image or video with AI",
    description="""
    Generate images with Imagen or videos with Veo.
    
    **Image Generation (Imagen):**
    - Synchronous operation - returns immediately with image URL
    - High quality image generation with prompt enhancement
    - Supports multiple aspect ratios (1:1, 16:9, 9:16)
    - Automatic upload to cloud storage with user/session isolation
    
    **Video Generation (Veo):**
    - Asynchronous operation - returns operation_id to poll for status
    - 8-second video generation
    - Text-to-video and image-to-video support
    - Poll /media/status/{operation_id} to check progress
    - Videos uploaded to storage when complete
    
    **Authentication Required:** JWT token via Supabase
    """,
    responses={
        200: {
            "description": "Generation started or completed successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "image_completed": {
                            "summary": "Image generation completed",
                            "value": {
                                "success": True,
                                "status": "completed",
                                "generated_asset": {
                                    "asset_id": "abc123",
                                    "content_type": "image",
                                    "file_path": "user_id/session_id/generated_image_abc123.png",
                                    "file_url": "https://storage.googleapis.com/.../generated_image_abc123.png",
                                    "prompt": "A serene mountain landscape",
                                    "width": 1920,
                                    "height": 1080,
                                    "duration_seconds": None,
                                    "file_size": 2458624
                                },
                                "operation_id": None,
                                "error_message": None
                            }
                        },
                        "video_started": {
                            "summary": "Video generation started",
                            "value": {
                                "success": True,
                                "status": "processing",
                                "generated_asset": None,
                                "operation_id": "projects/123/locations/us-central1/operations/456",
                                "error_message": None
                            }
                        }
                    }
                }
            }
        },
        401: {"description": "Unauthorized - invalid or missing JWT token"},
        400: {"description": "Bad request - invalid parameters"},
        500: {"description": "Internal server error - generation failed"}
    }
)
async def generate_media(
    request: MediaGenerationRequest,
    user_data: dict = Depends(get_current_user),
    media_service: MediaGenerationService = Depends(get_media_generation_service)
) -> MediaGenerationResponse:
    """Generate image or video with AI."""
    
    user_id = user_data.get("user_id")
    session_id = user_data.get("session_id")
    
    try:
        if request.content_type == "image":
            # Image generation (sync)
            logger.info(f"Image generation request from user {user_id}: {request.prompt[:50]}...")
            
            result = await media_service.generate_image(
                prompt=request.prompt,
                user_id=user_id,
                session_id=session_id,
                aspect_ratio=request.aspect_ratio
            )
            
            return MediaGenerationResponse(
                success=True,
                status="completed",
                generated_asset=GeneratedAsset(
                    asset_id=result.asset_id,
                    content_type=result.content_type,
                    file_path=result.file_path,
                    file_url=result.file_url,
                    prompt=result.prompt,
                    width=result.width,
                    height=result.height,
                    duration_seconds=result.duration_seconds,
                    file_size=result.file_size
                ),
                operation_id=None,
                error_message=None
            )
            
        elif request.content_type == "video":
            # Video generation (async)
            logger.info(f"Video generation request from user {user_id}: {request.prompt[:50]}...")
            
            operation_id = await media_service.generate_video(
                prompt=request.prompt,
                user_id=user_id,
                session_id=session_id,
                negative_prompt=request.negative_prompt,
                aspect_ratio=request.aspect_ratio,
                resolution=request.resolution,
                reference_image_url=request.reference_image_url
            )
            
            return MediaGenerationResponse(
                success=True,
                status="processing",
                generated_asset=None,
                operation_id=operation_id,
                error_message=None
            )
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid content_type: {request.content_type}"
            )
            
    except Exception as e:
        logger.error(f"Media generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/status/{operation_id:path}",
    response_model=VideoStatusResponse,
    summary="Check video generation status",
    description="""
    Poll the status of an asynchronous video generation operation.
    
    **Workflow:**
    1. Call POST /media/generate with content_type="video"
    2. Receive operation_id
    3. Poll this endpoint every 5-10 seconds
    4. When status="completed", retrieve generated_asset with video URL
    
    **Status Values:**
    - `processing`: Video is still being generated
    - `completed`: Video is ready, download from generated_asset.file_url
    - `failed`: Generation failed, see error_message
    
    **Authentication Required:** JWT token via Supabase
    """,
    responses={
        200: {
            "description": "Status retrieved successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "processing": {
                            "summary": "Still processing",
                            "value": {
                                "success": True,
                                "status": "processing",
                                "generated_asset": None,
                                "error_message": None
                            }
                        },
                        "completed": {
                            "summary": "Generation completed",
                            "value": {
                                "success": True,
                                "status": "completed",
                                "generated_asset": {
                                    "asset_id": "def456",
                                    "content_type": "video",
                                    "file_path": "user_id/session_id/generated_video_def456.mp4",
                                    "file_url": "https://storage.googleapis.com/.../generated_video_def456.mp4",
                                    "prompt": "A cat playing piano",
                                    "width": 1280,
                                    "height": 720,
                                    "duration_seconds": 8.0,
                                    "file_size": 5242880
                                },
                                "error_message": None
                            }
                        },
                        "failed": {
                            "summary": "Generation failed",
                            "value": {
                                "success": False,
                                "status": "failed",
                                "generated_asset": None,
                                "error_message": "Video generation timeout"
                            }
                        }
                    }
                }
            }
        },
        401: {"description": "Unauthorized - invalid or missing JWT token"},
        404: {"description": "Operation not found"},
        500: {"description": "Internal server error"}
    }
)
async def check_video_status(
    operation_id: str,
    user_data: dict = Depends(get_current_user),
    media_service: MediaGenerationService = Depends(get_media_generation_service)
) -> VideoStatusResponse:
    """Check status of video generation operation."""
    
    try:
        logger.info(f"Checking video status: {operation_id}")
        
        status_str, result, error_message = await media_service.check_video_status(
            operation_id=operation_id
        )
        
        if status_str == "completed" and result:
            return VideoStatusResponse(
                success=True,
                status="completed",
                generated_asset=GeneratedAsset(
                    asset_id=result.asset_id,
                    content_type=result.content_type,
                    file_path=result.file_path,
                    file_url=result.file_url,
                    prompt=result.prompt,
                    width=result.width,
                    height=result.height,
                    duration_seconds=result.duration_seconds,
                    file_size=result.file_size
                ),
                error_message=None
            )
        elif status_str == "failed":
            return VideoStatusResponse(
                success=False,
                status="failed",
                generated_asset=None,
                error_message=error_message
            )
        else:  # processing
            return VideoStatusResponse(
                success=True,
                status="processing",
                generated_asset=None,
                error_message=None
            )
            
    except ValueError as e:
        # Operation not found
        logger.warning(f"Operation not found: {operation_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Status check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/health",
    summary="Health check for media generation service",
    response_model=dict
)
async def health_check():
    """Check if media generation service is operational."""
    return {
        "status": "healthy",
        "service": "media_generation"
    }
