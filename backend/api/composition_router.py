"""
API router for composition generation endpoints.

This module provides REST API endpoints for generating and modifying video
compositions using AI.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict

from models.requests.CompositionGenerationRequest import CompositionGenerationRequest
from models.responses.CompositionGenerationResponse import CompositionGenerationResponse
from business_logic.generate_composition import CompositionGenerationService
from core.security import get_current_user
from core.dependencies import resolve_chat_provider


logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/generate",
    response_model=CompositionGenerationResponse,
    summary="Generate video composition from user prompt",
    description="""
    Generate or modify a video composition using AI based on user's natural language request.
    
    Features:
    - Create new compositions from scratch
    - Incrementally edit existing compositions
    - Use media from user's library
    - Maintain conversation context for iterative refinement
    - Support visual context (preview frame screenshots)
    
    The AI returns a structured composition blueprint compatible with Remotion.
    """,
    responses={
        200: {
            "description": "Composition generated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "composition_code": '[{"clips":[{"id":"clip-1","startTimeInSeconds":0,"endTimeInSeconds":5,"element":{"elements":["h1;id:title;parent:root;fontSize:48px;color:#fff;text:Hello World"]}}]}]',
                        "explanation": "Generated composition for: Add a title saying Hello World",
                        "duration": 5.0,
                        "model_used": "gemini-2.5-flash",
                        "error_message": None,
                        "metadata": {"tracks_count": 1}
                    }
                }
            }
        },
        400: {"description": "Invalid request parameters"},
        401: {"description": "Unauthorized - invalid or missing JWT token"},
        500: {"description": "Internal server error during generation"}
    }
)
async def generate_composition(
    request: CompositionGenerationRequest,
    user: Dict = Depends(get_current_user)
) -> CompositionGenerationResponse:
    """
    Generate or modify a video composition based on user request.
    
    Requires JWT authentication. User and session information is extracted
    from the JWT token for logging and tracking purposes.
    
    Supports dynamic provider selection (Gemini/Claude) via request.provider field.
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
            f"Composition generation request from user {user_id}, "
            f"session {session_id}, provider: {request.provider}: {request.user_request[:100]}"
        )
        
        # DEBUG: Log incoming provider and model name
        logger.info(f"🔍 DEBUG: Received provider={request.provider}, model_name={request.model_name}")
        
        # Resolve provider/model pairing based on request configuration
        chat_provider, effective_model_name = resolve_chat_provider(
            provider_name=request.provider,
            requested_model=request.model_name
        )
        
        # Create service with selected provider
        # NOTE: Cannot use Depends() here since provider comes from request body
        service = CompositionGenerationService(chat_provider=chat_provider)
        
        # Generate composition
        result = await service.generate_composition(
            user_request=request.user_request,
            preview_settings=request.preview_settings,
            user_id=user_id,
            session_id=session_id,
            media_library=request.media_library,
            current_composition=request.current_composition,
            preview_frame=request.preview_frame,
            model_name=effective_model_name,
            temperature=request.temperature
        )
        
        # Convert result to response
        return CompositionGenerationResponse(
            success=result.success,
            composition_code=result.composition_code,
            explanation=result.explanation,
            duration=result.duration,
            model_used=result.model_used,
            error_message=result.error_message,
            metadata=result.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Composition generation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate composition: {str(e)}"
        )


@router.get(
    "/health",
    summary="Health check for composition generation service",
    description="Verify that the composition generation service is operational"
)
async def health_check() -> Dict[str, str]:
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "service": "composition_generation"
    }
