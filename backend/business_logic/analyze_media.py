"""
Media Analysis Service - Business Logic Layer.

Orchestrates media analysis operations using MediaAnalysisProvider and StorageProvider.
This service handles the business logic for analyzing images, videos, audio, and documents
using AI-powered multimodal analysis.
"""

import logging
import time
import asyncio
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

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
    audio_timestamp: bool = False


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
        temperature: float = 0.1,
        audio_timestamp: bool = False
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
            audio_timestamp: Request timestamps for audio-only media when supported
        
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
        logger.debug(f"File URL: {file_url[:120]}...")
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
            
            # Perform analysis using the provider with duration tracking
            t0 = time.monotonic()
            result = await self.media_provider.analyze_media(
                file_url=file_url,
                question=question,
                model_name=model_name,
                temperature=temperature,
                audio_timestamp=audio_timestamp
            )
            duration_s = round(time.monotonic() - t0, 3)
            
            if result.success:
                logger.info(
                    f"Analysis successful for user={user_id}, session={session_id}, "
                    f"tokens={result.metadata.get('total_tokens', 0)}, duration_s={duration_s}"
                )
            else:
                logger.warning(
                    f"Analysis failed for user={user_id}, session={session_id}: "
                    f"{result.error_message} (duration_s={duration_s})"
                )
            
            # Persist a JSON log entry for this analysis for end-to-end tracing
            try:
                from pathlib import Path
                from datetime import datetime
                logs_dir = Path(__file__).parent.parent / "logs"
                logs_dir.mkdir(exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                analysis_log = logs_dir / f"media_analysis_{session_id}_{timestamp}.json"
                with open(analysis_log, "w") as f:
                    import json as _json
                    _json.dump({
                        "user_id": user_id,
                        "session_id": session_id,
                        "timestamp": timestamp,
                        "file_url": file_url,
                        "question": question,
                        "model_used": result.model_used,
                        "temperature": temperature,
                        "audio_timestamp": audio_timestamp,
                        "success": result.success,
                        "error_message": result.error_message,
                        "metadata": result.metadata,
                        "duration_seconds": duration_s
                    }, f, indent=2)
                logger.info(f"💾 Saved media analysis log to: {analysis_log}")
            except Exception as log_err:
                logger.warning(f"Could not write media analysis log: {log_err}")
            
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
    
    async def analyze_media_batch(
        self,
    videos: List[Dict[str, Any]],
        question: Optional[str] = None,
        user_id: str = None,
        session_id: str = None,
        model_name: Optional[str] = None,
        temperature: float = 0.1,
        max_concurrent: int = 4,
        audio_timestamp: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Analyze multiple videos in parallel using concurrent requests.
        
        Args:
            videos: List of dicts with 'file_url', optional 'title', and optional 'question' keys
            question: Global question to ask about each video (optional if per-video questions provided)
            user_id: User ID (for logging/tracking)
            session_id: Session ID (for logging/tracking)
            model_name: Optional model override
            temperature: Generation temperature (0.0-1.0)
            max_concurrent: Maximum number of concurrent analysis requests (1-10)
            audio_timestamp: Optional global toggle for requesting timestamps on audio-only files
        
        Returns:
            Dict with:
                - aggregated_analysis: Single formatted string with all analyses
                - results: List of per-video results
                - total_videos: Total count
                - successful_count: Success count
                - failed_count: Failure count
                - total_metadata: Aggregated stats (tokens, duration)
        
        Example:
            result = await service.analyze_media_batch(
                videos=[
                    {"file_url": "gs://bucket/v1.mp4", "title": "Intro", "question": "What's shown?"},
                    {"file_url": "gs://bucket/v2.mp4", "title": "Demo", "question": "Describe the demo"}
                ],
                user_id="user123",
                session_id="session456",
                max_concurrent=4
            )
        """
        logger.info(
            f"Starting batch media analysis: {len(videos)} videos, "
            f"max_concurrent={max_concurrent}, user={user_id}, session={session_id}"
        )
        
        if not videos:
            raise ValueError("videos list cannot be empty")
        
        if max_concurrent < 1 or max_concurrent > 10:
            raise ValueError("max_concurrent must be between 1 and 10")
        
        # Enforce batch size limit
        if len(videos) > 10:
            raise ValueError("Maximum 10 videos per batch request")
        
        batch_start = time.monotonic()
        
        # Create analysis tasks for each video
        async def analyze_single_video(idx: int, video: Dict[str, str]) -> Dict[str, Any]:
            """Analyze a single video and return structured result."""
            file_url = video.get("file_url")
            title = video.get("title") or f"Video {idx + 1}"
            # Use per-video question if provided, otherwise fall back to global question, otherwise use default
            video_question = video.get("question") or question or "Describe what you see in this media."
            video_audio_flag = video.get("audio_timestamp")
            effective_audio_timestamp = (
                bool(video_audio_flag)
                if video_audio_flag is not None
                else bool(audio_timestamp)
            )
            
            logger.debug(f"Starting analysis {idx+1}/{len(videos)}: {title}")
            
            try:
                result = await self.analyze_media(
                    file_url=file_url,
                    question=video_question,
                    user_id=user_id,
                    session_id=f"{session_id}_batch_{idx}",
                    model_name=model_name,
                    temperature=temperature,
                    audio_timestamp=effective_audio_timestamp
                )
                
                return {
                    "file_url": file_url,
                    "title": title,
                    "success": result.success,
                    "analysis": result.analysis if result.success else None,
                    "error_message": result.error_message if not result.success else None,
                    "metadata": result.metadata,
                    "audio_timestamp": effective_audio_timestamp
                }
            
            except Exception as e:
                logger.error(f"Error analyzing video {idx+1} ({title}): {e}", exc_info=True)
                return {
                    "file_url": file_url,
                    "title": title,
                    "success": False,
                    "analysis": None,
                    "error_message": f"Analysis failed: {str(e)}",
                    "metadata": None,
                    "audio_timestamp": effective_audio_timestamp
                }
        
        # Run analyses with concurrency limit using semaphore
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def analyze_with_limit(idx: int, video: Dict[str, str]) -> Dict[str, Any]:
            """Wrapper to enforce concurrency limit."""
            async with semaphore:
                return await analyze_single_video(idx, video)
        
        # Execute all analyses concurrently
        tasks = [analyze_with_limit(i, video) for i, video in enumerate(videos)]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        
        batch_duration = round(time.monotonic() - batch_start, 3)
        
        # Aggregate results
        successful_count = sum(1 for r in results if r["success"])
        failed_count = len(results) - successful_count
        
        # Calculate total tokens
        total_tokens = 0
        for r in results:
            if r.get("metadata") and isinstance(r["metadata"], dict):
                total_tokens += r["metadata"].get("total_tokens", 0)
        
        # Format aggregated analysis string
        aggregated_parts = []
        for i, result in enumerate(results):
            title = result["title"]
            if result["success"]:
                analysis_text = result["analysis"] or "(No analysis returned)"
            else:
                analysis_text = f"ERROR: {result['error_message']}"
            
            aggregated_parts.append(f"Media {i+1} ({title}): {analysis_text}")
        
        aggregated_analysis = "\n\n".join(aggregated_parts)
        
        logger.info(
            f"Batch analysis complete: {successful_count}/{len(videos)} successful, "
            f"total_tokens={total_tokens}, duration={batch_duration}s"
        )

        # Determine effective question for logging/reporting
        effective_question = question
        if not effective_question:
            for video in videos:
                if video.get("question"):
                    effective_question = video["question"]
                    break
        if not effective_question:
            effective_question = "Describe what you see in this media."
        
        # Persist batch log
        try:
            from pathlib import Path
            from datetime import datetime
            logs_dir = Path(__file__).parent.parent / "logs"
            logs_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            batch_log = logs_dir / f"batch_analysis_{session_id}_{timestamp}.json"
            with open(batch_log, "w") as f:
                import json as _json
                _json.dump({
                    "user_id": user_id,
                    "session_id": session_id,
                    "timestamp": timestamp,
                    "question": effective_question,
                    "model_used": model_name or self.media_provider.default_model,
                    "temperature": temperature,
                    "total_videos": len(videos),
                    "successful_count": successful_count,
                    "failed_count": failed_count,
                    "total_tokens": total_tokens,
                    "duration_seconds": batch_duration,
                    "max_concurrent": max_concurrent,
                    "audio_timestamp": audio_timestamp,
                    "results": results
                }, f, indent=2)
            logger.info(f"💾 Saved batch analysis log to: {batch_log}")
        except Exception as log_err:
            logger.warning(f"Could not write batch analysis log: {log_err}")
        
        return {
            "aggregated_analysis": aggregated_analysis,
            "results": results,
            "question": effective_question,
            "total_videos": len(videos),
            "successful_count": successful_count,
            "failed_count": failed_count,
            "total_metadata": {
                "total_tokens": total_tokens,
                "duration_seconds": batch_duration,
                "max_concurrent": max_concurrent
            }
        }
