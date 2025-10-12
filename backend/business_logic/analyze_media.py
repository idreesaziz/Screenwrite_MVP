"""
Media Analysis Service - Business Logic Layer.

Orchestrates media analysis operations using MediaAnalysisProvider and StorageProvider.
This service handles the business logic for analyzing images, videos, audio, and documents
using AI-powered multimodal analysis.
"""

import logging
from typing import Optional
from dataclasses import dataclass

from services.base.MediaAnalysisProvider import MediaAnalysisProvider, MediaAnalysisResult
from services.base.StorageProvider import StorageProvider

logger = logging.getLogger(__name__)


@dataclass
class MediaAnalysisRequest:
    """Request data for media analysis."""
    file_url: str
    question: str
    user_id: str
    session_id: str
    model_name: Optional[str] = None
    temperature: float = 0.1


class MediaAnalysisService:
    """
    Service for AI-powered media analysis.
    
    This service orchestrates media analysis operations by:
    1. Validating file URLs (GCS URIs or HTTP URLs)
    2. Using MediaAnalysisProvider for AI analysis
    3. Optionally verifying file existence via StorageProvider
    
    Dependencies are injected to support multiple providers (Gemini, Claude, etc.).
    """
    
    def __init__(
        self,
        media_analysis_provider: MediaAnalysisProvider,
        storage_provider: Optional[StorageProvider] = None
    ):
        """
        Initialize the media analysis service.
        
        Args:
            media_analysis_provider: Provider for AI-powered media analysis
            storage_provider: Optional provider for storage operations (file verification)
        """
        self.media_provider = media_analysis_provider
        self.storage_provider = storage_provider
        logger.info(f"MediaAnalysisService initialized with provider: {type(media_analysis_provider).__name__}")
    
    async def analyze_media(
        self,
        file_url: str,
        question: str,
        user_id: str,
        session_id: str,
        model_name: Optional[str] = None,
        temperature: float = 0.1
    ) -> MediaAnalysisResult:
        """
        Analyze media file using AI.
        
        Args:
            file_url: GCS URI (gs://bucket/path) or HTTP/HTTPS URL (signed URL)
            question: Question to ask about the media
            user_id: User ID (for logging/tracking)
            session_id: Session ID (for logging/tracking)
            model_name: Optional model override (e.g., "gemini-2.5-flash")
            temperature: Generation temperature (0.0-1.0)
        
        Returns:
            MediaAnalysisResult with analysis or error information
        
        Example:
            result = await service.analyze_media(
                file_url="gs://my-bucket/video.mp4",
                question="What is happening in this video?",
                user_id="user123",
                session_id="session456"
            )
        """
        logger.info(f"Starting media analysis for user={user_id}, session={session_id}")
        logger.debug(f"File URL: {file_url[:80]}...")
        logger.debug(f"Question: {question}")
        
        try:
            # Validate inputs
            if not file_url or not question:
                raise ValueError("file_url and question are required")
            
            if not user_id or not session_id:
                raise ValueError("user_id and session_id are required")
            
            # Optional: Verify file exists (if storage provider is available)
            if self.storage_provider and file_url.startswith("gs://"):
                try:
                    # Extract bucket and path from gs:// URI
                    # Format: gs://bucket-name/path/to/file.ext
                    uri_parts = file_url[5:].split('/', 1)
                    if len(uri_parts) == 2:
                        bucket_name, file_path = uri_parts
                        exists = await self.storage_provider.file_exists(file_path)
                        if not exists:
                            logger.warning(f"File may not exist in GCS: {file_url}")
                except Exception as e:
                    logger.warning(f"Could not verify file existence: {e}")
            
            # Perform analysis using the provider
            result = await self.media_provider.analyze_media(
                file_url=file_url,
                question=question,
                model_name=model_name,
                temperature=temperature
            )
            
            if result.success:
                logger.info(
                    f"Analysis successful for user={user_id}, session={session_id}, "
                    f"tokens={result.metadata.get('total_tokens', 0)}"
                )
            else:
                logger.warning(
                    f"Analysis failed for user={user_id}, session={session_id}: "
                    f"{result.error_message}"
                )
            
            return result
        
        except ValueError as e:
            # Validation errors
            error_msg = str(e)
            logger.error(f"Validation error: {error_msg}")
            return MediaAnalysisResult(
                analysis="",
                model_used=model_name or self.media_provider.default_model,
                file_url=file_url,
                question=question,
                success=False,
                error_message=f"Invalid request: {error_msg}"
            )
        
        except Exception as e:
            # Unexpected errors
            error_msg = str(e)
            logger.error(f"Unexpected error in media analysis: {error_msg}", exc_info=True)
            return MediaAnalysisResult(
                analysis="",
                model_used=model_name or self.media_provider.default_model,
                file_url=file_url,
                question=question,
                success=False,
                error_message=f"Analysis failed: {error_msg}"
            )
    
    async def is_file_ready(self, file_url: str) -> bool:
        """
        Check if a file is ready for analysis.
        
        For GCS files, this always returns True (files are ready once uploaded).
        For other file types, delegates to the provider.
        
        Args:
            file_url: File URL to check
        
        Returns:
            True if file is ready for analysis
        """
        try:
            return await self.media_provider.is_file_ready(file_url)
        except Exception as e:
            logger.warning(f"Error checking file readiness: {e}")
            return True  # Assume ready if check fails
    
    async def get_supported_file_types(self) -> list[str]:
        """
        Get list of supported MIME types for media analysis.
        
        Returns:
            List of supported MIME types
        """
        return await self.media_provider.get_supported_file_types()
