"""
Media Analysis API Router.

Handles endpoints for AI-powered analysis of images, videos, audio, and documents.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict

from models.requests.MediaAnalysisRequest import MediaAnalysisRequest
from models.responses.MediaAnalysisResponse import MediaAnalysisResponse
from business_logic.analyze_media import MediaAnalysisService
from core.dependencies import get_media_analysis_service
from core.security import get_current_user

logger = logging.getLogger(__name__)

# Create router without prefix (prefix is added in main.py)
router = APIRouter(
    tags=["Media Analysis"]
)


@router.post("/media", response_model=MediaAnalysisResponse)
async def analyze_media(
    request: MediaAnalysisRequest,
    user: Dict = Depends(get_current_user),
    service: MediaAnalysisService = Depends(get_media_analysis_service)
) -> MediaAnalysisResponse:
    """
    Analyze media content using AI.
    
    Supports analysis of:
    - Videos (MP4, MOV, AVI, WebM, etc.)
    - Images (JPEG, PNG, WebP, GIF, etc.)
    - Audio (MP3, WAV, AAC, etc.)
    - Documents (PDF, TXT, etc.)
    
    **Authentication Required**: Bearer token (JWT)
    
    **Parameters:**
    - `file_url`: GCS URI (gs://bucket/path) or HTTP/HTTPS URL (signed URL)
    - `question`: Question to ask about the media content
    - `model_name`: Optional model override (default: gemini-2.0-flash-exp)
    - `temperature`: Generation temperature 0.0-1.0 (default: 0.1)
    
    **Returns:**
    - `success`: Whether analysis succeeded
    - `analysis`: AI-generated analysis text
    - `model_used`: Model that performed the analysis
    - `error_message`: Error details if failed
    - `metadata`: Token usage and other metadata
    
    **Example Request:**
    ```json
    {
      "file_url": "gs://my-bucket/videos/sample.mp4",
      "question": "What activities are shown in this video?",
      "temperature": 0.1
    }
    ```
    
    **Example Response:**
    ```json
    {
      "success": true,
      "analysis": "The video shows surfers riding waves...",
      "model_used": "gemini-2.0-flash-exp",
      "file_url": "gs://my-bucket/videos/sample.mp4",
      "question": "What activities are shown in this video?",
      "metadata": {
        "prompt_tokens": 4657,
        "response_tokens": 152,
        "total_tokens": 4809
      }
    }
    ```
    """
    # Extract user info from JWT
    user_id = user.get("user_id")
    session_id = user.get("session_id")
    
    if not user_id or not session_id:
        logger.error("Invalid JWT: missing user_id or session_id")
        raise HTTPException(
            status_code=400,
            detail="Invalid JWT: missing user_id or session_id"
        )
    
    logger.info(f"Media analysis request from user={user_id}, session={session_id}")
    
    try:
        # Call business logic service
        result = await service.analyze_media(
            file_url=request.file_url,
            question=request.question,
            user_id=user_id,
            session_id=session_id,
            model_name=request.model_name,
            temperature=request.temperature
        )
        
        # Convert to response model
        return MediaAnalysisResponse(
            success=result.success,
            analysis=result.analysis,
            model_used=result.model_used,
            file_url=result.file_url,
            question=result.question,
            error_message=result.error_message,
            metadata=result.metadata
        )
    
    except Exception as e:
        logger.error(f"Unexpected error in analyze_media endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/supported-types")
async def get_supported_file_types(
    service: MediaAnalysisService = Depends(get_media_analysis_service)
) -> Dict[str, list]:
    """
    Get list of supported media file types.
    
    Returns a list of MIME types that can be analyzed by the media analysis service.
    
    **Authentication**: Not required (public endpoint)
    
    **Returns:**
    ```json
    {
      "supported_types": [
        "video/mp4",
        "image/jpeg",
        "audio/mp3",
        ...
      ]
    }
    ```
    """
    try:
        supported_types = await service.get_supported_file_types()
        return {"supported_types": supported_types}
    except Exception as e:
        logger.error(f"Error getting supported file types: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get supported file types: {str(e)}"
        )
