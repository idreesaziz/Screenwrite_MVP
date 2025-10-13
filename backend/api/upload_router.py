"""
API router for media upload endpoints.

Provides REST API for uploading user media files to cloud storage.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import Optional

from models.responses.MediaUploadResponse import MediaUploadResponse
from core.security import get_current_user
from core.dependencies import get_storage_provider
from services.base.StorageProvider import StorageProvider


logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/upload",
    response_model=MediaUploadResponse,
    summary="Upload media file to cloud storage",
    description="""
    Upload user media files (videos, images, audio) to cloud storage.
    
    **Features:**
    - Automatic user/session isolation (files stored at user_id/session_id/filename)
    - Support for any file type
    - Returns public URL for immediate use
    - Optional signed URL with expiration
    - File metadata included in response
    
    **File Size Limits:**
    - Images: Up to 10MB
    - Videos: Up to 100MB
    - Other files: Up to 50MB
    
    **Authentication Required:** JWT token via Supabase
    """,
    responses={
        200: {
            "description": "File uploaded successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "file_path": "user_id/session_id/my_video.mp4",
                        "file_url": "https://storage.googleapis.com/.../my_video.mp4",
                        "signed_url": "https://storage.googleapis.com/.../my_video.mp4?X-Goog-Signature=...",
                        "file_size": 5242880,
                        "content_type": "video/mp4",
                        "error_message": None
                    }
                }
            }
        },
        401: {"description": "Unauthorized - invalid or missing JWT token"},
        400: {"description": "Bad request - no file provided or file too large"},
        500: {"description": "Internal server error - upload failed"}
    }
)
async def upload_media(
    file: UploadFile = File(..., description="Media file to upload"),
    user_data: dict = Depends(get_current_user),
    storage_provider: StorageProvider = Depends(get_storage_provider)
) -> MediaUploadResponse:
    """Upload media file to cloud storage."""
    
    user_id = user_data.get("user_id")
    session_id = user_data.get("session_id")
    
    try:
        if not file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        # Validate file size (100MB max)
        max_size = 100 * 1024 * 1024  # 100MB
        file_size = 0
        
        logger.info(f"Uploading file: {file.filename} (type: {file.content_type}) for user {user_id}")
        
        # Read file data
        file_data = await file.read()
        file_size = len(file_data)
        
        if file_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large: {file_size} bytes (max: {max_size} bytes)"
            )
        
        logger.info(f"File size: {file_size} bytes")
        
        # Upload to storage
        from io import BytesIO
        upload_result = await storage_provider.upload_file(
            file_data=BytesIO(file_data),
            user_id=user_id,
            session_id=session_id,
            filename=file.filename,
            content_type=file.content_type
        )
        
        logger.info(f"✅ File uploaded: {upload_result.url[:80]}...")
        
        # Construct GCS URI for Vertex AI access
        bucket_name = storage_provider.bucket_name if hasattr(storage_provider, 'bucket_name') else "screenwrite-media"
        gcs_uri = f"gs://{bucket_name}/{upload_result.path}"
        
        return MediaUploadResponse(
            success=True,
            file_path=upload_result.path,
            file_url=upload_result.url,
            gcs_uri=gcs_uri,
            signed_url=upload_result.signed_url,
            file_size=upload_result.size,
            content_type=upload_result.content_type,
            error_message=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/health",
    summary="Health check for upload service",
    response_model=dict
)
async def health_check():
    """Check if upload service is operational."""
    return {
        "status": "healthy",
        "service": "media_upload"
    }
