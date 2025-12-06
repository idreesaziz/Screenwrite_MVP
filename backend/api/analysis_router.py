"""
Media Analysis API Router.

Handles endpoints for AI-powered analysis of images, videos, audio, and documents.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict

from models.requests.BatchMediaAnalysisRequest import BatchMediaAnalysisRequest
from models.responses.BatchMediaAnalysisResponse import BatchMediaAnalysisResponse, VideoAnalysisResult
from business_logic.analyze_media import MediaAnalysisService
from core.dependencies import get_media_analysis_service
from core.security import get_current_user

logger = logging.getLogger(__name__)

# Create router without prefix (prefix is added in main.py)
router = APIRouter(
    tags=["Media Analysis"]
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


@router.post("/media/batch", response_model=BatchMediaAnalysisResponse)
async def analyze_media_batch(
    request: BatchMediaAnalysisRequest,
    user: Dict = Depends(get_current_user),
    service: MediaAnalysisService = Depends(get_media_analysis_service)
) -> BatchMediaAnalysisResponse:
    """
    Analyze multiple videos in parallel using concurrent requests.
    
    This endpoint processes 3-4 videos simultaneously, significantly reducing
    total analysis time compared to sequential processing.
    
    **Authentication Required**: Bearer token (JWT)
    
    **Parameters:**
    - `videos`: Array of video objects with `file_url` and optional `title`
    - `question`: Question to ask about each video
    - `model_name`: Optional model override (default: gemini-2.0-flash-exp)
    - `temperature`: Generation temperature 0.0-1.0 (default: 0.1)
    - `max_concurrent`: Max parallel requests (1-10, default: 4)
    
    **Returns:**
    - `success`: Whether batch completed (true even if some videos failed)
    - `aggregated_analysis`: Single formatted string: "Video 1 (Title): analysis..."
    - `results`: Per-video results with success/error details
    - `total_videos`: Count of videos processed
    - `successful_count`: Number of successful analyses
    - `failed_count`: Number of failed analyses
    - `total_metadata`: Aggregated stats (tokens, duration)
    
    **Example Request:**
    ```json
    {
      "videos": [
        {
          "file_url": "gs://bucket/video1.mp4",
          "title": "Intro"
        },
        {
          "file_url": "gs://bucket/video2.mp4",
          "title": "Demo"
        },
        {
          "file_url": "gs://bucket/video3.mp4",
          "title": "Outro"
        }
      ],
      "question": "What activities are shown?",
      "temperature": 0.1,
      "max_concurrent": 4
    }
    ```
    
    **Example Response:**
    ```json
    {
      "success": true,
      "aggregated_analysis": "Video 1 (Intro): The video shows...\\n\\nVideo 2 (Demo): ...\\n\\nVideo 3 (Outro): ...",
      "results": [
        {
          "file_url": "gs://bucket/video1.mp4",
          "title": "Intro",
          "success": true,
          "analysis": "The video shows...",
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
    ```
    
    **Performance Notes:**
    - Recommended: 3-4 videos per request for optimal latency/throughput balance
    - Maximum: 10 videos per request
    - Concurrency limit prevents API rate limiting and quota issues
    - Individual video failures don't cancel the entire batch
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
    
    logger.info(
        f"Batch media analysis request from user={user_id}, session={session_id}, "
        f"videos={len(request.videos)}, max_concurrent={request.max_concurrent}"
    )
    
    # Debug logging
    logger.info(f"Request videos: {[(v.file_url[:50], v.title, bool(v.question)) for v in request.videos]}")
    logger.info(f"Global question: {request.question}")
    
    try:
        # Convert request videos to dict format (include per-video questions)
        videos = [
            {
                "file_url": v.file_url, 
                "title": v.title,
                "question": v.question,
                "audio_timestamp": v.audio_timestamp
            }
            for v in request.videos
        ]
        
        # Call business logic service
        batch_result = await service.analyze_media_batch(
            videos=videos,
            question=request.question,  # Global fallback question
            user_id=user_id,
            session_id=session_id,
            model_name=request.model_name,
            temperature=request.temperature,
            max_concurrent=request.max_concurrent,
            audio_timestamp=request.audio_timestamp
        )
        
        # Determine question to return (prefer service result, fall back to request, then first per-video, then default)
        response_question = batch_result.get("question") or request.question
        if not response_question:
            for v in request.videos:
                if v.question:
                    response_question = v.question
                    break
        if not response_question:
            response_question = "Describe what you see in this media."

        # Convert results to response models
        video_results = [
            VideoAnalysisResult(
                file_url=r["file_url"],
                title=r["title"],
                success=r["success"],
                analysis=r.get("analysis"),
                error_message=r.get("error_message"),
                metadata=r.get("metadata"),
                audio_timestamp=r.get("audio_timestamp")
            )
            for r in batch_result["results"]
        ]
        
        return BatchMediaAnalysisResponse(
            success=True,
            aggregated_analysis=batch_result["aggregated_analysis"],
            results=video_results,
            model_used=request.model_name or service.media_provider.default_model,
            question=response_question,
            total_videos=batch_result["total_videos"],
            successful_count=batch_result["successful_count"],
            failed_count=batch_result["failed_count"],
            total_metadata=batch_result["total_metadata"]
        )
    
    except ValueError as e:
        logger.error(f"Validation error in batch analysis: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(f"Unexpected error in analyze_media_batch endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
