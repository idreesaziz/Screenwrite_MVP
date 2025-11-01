"""Google Veo video generation implementation."""

import os
import io
import logging
import tempfile
import uuid
from typing import Optional
from datetime import datetime
from PIL import Image
from google import genai
from google.genai import types
from google.cloud import storage
import asyncio
from functools import wraps

from services.base.VideoGenerationProvider import (
    VideoGenerationProvider,
    VideoGenerationOperation,
    GeneratedVideo
)

logger = logging.getLogger(__name__)


def async_wrap(func):
    """Decorator to run sync operations in executor."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
    return wrapper


class VEOGenerationProvider(VideoGenerationProvider):
    """
    Google Veo video generation implementation.
    
    Features:
    - 8-second video generation
    - Text-to-video and image-to-video
    - Fast model (veo-3.0-fast-generate-001)
    - Async operation with polling
    - 720p and 1080p support
    - 16:9 and 9:16 aspect ratios
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        location: str = "us-central1",
        model_name: str = "veo-3.0-fast-generate-001",
        credentials_path: Optional[str] = None,
        gcs_bucket: Optional[str] = None
    ):
        """
        Initialize Veo video generation provider.
        
        Args:
            project_id: GCP project ID (uses env var if not provided)
            location: GCP region
            model_name: Veo model to use (default: fast model)
            credentials_path: Path to service account JSON (uses ADC if not provided)
            gcs_bucket: Default GCS bucket for uploads (optional)
        """
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT')
        self.location = location
        self.model_name = model_name
        self.gcs_bucket = gcs_bucket or os.getenv('GCS_BUCKET_NAME', 'screenwrite-media')
        
        # Initialize Vertex AI client using v1 API (Veo is on stable v1 now)
        self.client = genai.Client(
            http_options=types.HttpOptions(api_version="v1")
        )
        
        # Initialize GCS client for optional uploads
        self.storage_client = storage.Client()
        
        logger.info(f"VEOGenerationProvider initialized: model={model_name}, project={self.project_id}, gcs_bucket={self.gcs_bucket}")
    
    def _format_reference_image(self, reference_image: Image.Image) -> types.Image:
        """Convert PIL Image to Google API Image format."""
        try:
            # Convert PIL Image to bytes
            img_buffer = io.BytesIO()
            reference_image.save(img_buffer, format='PNG')
            img_bytes = img_buffer.getvalue()
            
            # Create Google API image object
            formatted_image = types.Image(
                image_bytes=img_bytes,
                mime_type="image/png"
            )
            logger.info("Successfully formatted reference image for Veo")
            return formatted_image
            
        except Exception as e:
            logger.error(f"Failed to format reference image: {e}")
            raise ValueError(f"Could not format reference image: {e}")
    
    async def generate_video(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        aspect_ratio: str = "16:9",
        resolution: str = "720p",
        reference_image: Optional[Image.Image] = None,
        **kwargs
    ) -> VideoGenerationOperation:
        """Start async video generation with Veo."""
        def _sync_generate():
            try:
                # Build generation config - include output_gcs_uri to ensure Vertex writes to our bucket
                config = types.GenerateVideosConfig(
                    output_gcs_uri=f"gs://{self.gcs_bucket}/tmp/veo/",
                    negative_prompt=negative_prompt,
                    aspect_ratio=aspect_ratio,
                    resolution=resolution,
                    number_of_videos=1
                )
                
                # Format reference image if provided
                formatted_image = None
                if reference_image:
                    formatted_image = self._format_reference_image(reference_image)
                
                # Start video generation (async operation)
                # aspect_ratio and resolution are direct parameters
                operation = self.client.models.generate_videos(
                    model=self.model_name,
                    prompt=prompt,
                    image=formatted_image,  # For image-to-video
                    config=config
                )
                
                logger.info(f"Video generation started: {operation.name}")
                
                # Create operation object
                return VideoGenerationOperation(
                    operation_id=operation.name,
                    prompt=prompt,
                    status="processing",
                    started_at=datetime.utcnow(),
                    metadata={
                        "aspect_ratio": aspect_ratio,
                        "resolution": resolution,
                        "negative_prompt": negative_prompt,
                        "has_reference_image": reference_image is not None
                    },
                    _operation_obj=operation  # Store internal operation
                )
                
            except Exception as e:
                logger.error(f"Video generation failed: {e}")
                raise RuntimeError(f"Failed to start video generation: {e}")
        
        return await async_wrap(_sync_generate)()
    
    async def check_generation_status(
        self,
        operation: VideoGenerationOperation,
        **kwargs
    ) -> VideoGenerationOperation:
        """Check status of video generation operation."""
        def _sync_check():
            try:
                # Get the stored operation object
                internal_op = operation._operation_obj
                if not internal_op:
                    raise ValueError("Operation object not found")
                
                # Refresh operation status
                updated_op = self.client.operations.get(operation=internal_op)
                
                # Update operation status
                if updated_op.done:
                    if hasattr(updated_op, 'error') and updated_op.error:
                        operation.status = "failed"
                        operation.error_message = str(updated_op.error)
                        operation.completed_at = datetime.utcnow()
                        logger.error(f"Video generation failed: {operation.error_message}")
                    else:
                        operation.status = "completed"
                        operation.completed_at = datetime.utcnow()
                        logger.info(f"Video generation completed: {operation.operation_id}")
                else:
                    operation.status = "processing"
                    logger.debug(f"Video generation still processing: {operation.operation_id}")
                
                # Update internal operation object
                operation._operation_obj = updated_op
                
                return operation
                
            except Exception as e:
                logger.error(f"Status check failed: {e}")
                raise RuntimeError(f"Failed to check generation status: {e}")
        
        return await async_wrap(_sync_check)()
    
    async def download_generated_video(
        self,
        operation: VideoGenerationOperation,
        upload_to_gcs: bool = False,
        gcs_path: Optional[str] = None,
        gcs_bucket: Optional[str] = None,
        **kwargs
    ) -> GeneratedVideo:
        """
        Download completed video and optionally upload to GCS.
        
        Args:
            operation: Completed VideoGenerationOperation
            upload_to_gcs: Whether to upload to GCS (default: False)
            gcs_path: Optional GCS path prefix (e.g., 'user_id/session_id')
            gcs_bucket: Optional GCS bucket (uses default if not provided)
            **kwargs: Additional parameters
            
        Returns:
            GeneratedVideo with video bytes and optional GCS URLs
        """
        def _sync_download():
            try:
                # Verify operation is completed
                if operation.status != "completed":
                    raise ValueError(f"Operation not completed. Status: {operation.status}")
                
                # Get internal operation object
                internal_op = operation._operation_obj
                if not internal_op:
                    raise ValueError("Operation object not found")
                
                # Get generated videos from result (preferred) or response (fallback)
                container = getattr(internal_op, 'result', None) or getattr(internal_op, 'response', None)
                if not container or not hasattr(container, 'generated_videos'):
                    raise ValueError("No generated videos found in operation result")
                generated_videos = container.generated_videos
                if not generated_videos or len(generated_videos) == 0:
                    raise ValueError("No generated videos found")
                
                generated_video = generated_videos[0]
                
                logger.info(f"Downloading generated video: {operation.operation_id}")
                
                # The SDK wraps the response - access the video object
                video_obj = generated_video.video if hasattr(generated_video, 'video') else generated_video
                
                video_data: bytes
                # Prefer downloading from GCS URI if present
                gcs_uri = getattr(video_obj, 'uri', None)
                if gcs_uri:
                    logger.info(f"Video available at: {gcs_uri}")
                    if not gcs_uri.startswith('gs://'):
                        raise ValueError(f"Invalid GCS URI format: {gcs_uri}")
                    parts = gcs_uri[5:].split('/', 1)  # Remove gs:// and split
                    source_bucket_name = parts[0]
                    source_blob_name = parts[1] if len(parts) > 1 else ''
                    # Download from GCS
                    logger.info(f"Downloading from GCS: {source_bucket_name}/{source_blob_name}")
                    source_bucket = self.storage_client.bucket(source_bucket_name)
                    source_blob = source_bucket.blob(source_blob_name)
                    video_data = source_blob.download_as_bytes()
                else:
                    # Fallback: Use inline bytes if provided by SDK
                    video_bytes = getattr(video_obj, 'video_bytes', None)
                    if not video_bytes:
                        raise ValueError("No URI or inline video bytes present in generated video response")
                    video_data = video_bytes
                file_size = len(video_data)
                
                logger.info(f"Video downloaded successfully: {file_size} bytes")
                
                # Get dimensions from metadata
                resolution = operation.metadata.get("resolution", "720p")
                width = 1280 if resolution == "720p" else 1920
                height = 720 if resolution == "720p" else 1080
                
                logger.info(f"Video downloaded successfully: {file_size} bytes")
                
                # Create base result
                result = GeneratedVideo(
                    video_data=video_data,
                    prompt=operation.prompt,
                    duration_seconds=8.0,  # Veo generates 8-second videos
                    width=width,
                    height=height,
                    file_size=file_size,
                    format="mp4",
                    metadata=operation.metadata or {}
                )
                
                # Upload to GCS if requested
                if upload_to_gcs:
                    bucket_name = gcs_bucket or self.gcs_bucket
                    
                    # Generate unique filename
                    asset_id = str(uuid.uuid4())
                    file_name = f"generated_video_{asset_id}.mp4"
                    
                    if gcs_path:
                        blob_name = f"{gcs_path}/{file_name}"
                    else:
                        blob_name = f"generated_videos/{file_name}"
                    
                    logger.info(f"Uploading to GCS: gs://{bucket_name}/{blob_name}")
                    
                    bucket = self.storage_client.bucket(bucket_name)
                    blob = bucket.blob(blob_name)
                    
                    blob.upload_from_string(video_data, content_type="video/mp4")
                    
                    # Generate signed URL (7 days expiration)
                    signed_url = blob.generate_signed_url(
                        version="v4",
                        expiration=7 * 24 * 60 * 60,  # 7 days
                        method="GET"
                    )
                    
                    # Update metadata with GCS info
                    result.metadata['gcs_uri'] = f"gs://{bucket_name}/{blob_name}"
                    result.metadata['gcs_signed_url'] = signed_url
                    result.metadata['gcs_public_url'] = blob.public_url
                    
                    logger.info(f"Upload complete: {signed_url[:80]}...")
                
                return result
                
            except Exception as e:
                logger.error(f"Failed to download video: {e}")
                raise RuntimeError(f"Failed to download generated video: {e}")
        
        return await async_wrap(_sync_download)()
    
    async def cancel_generation(
        self,
        operation: VideoGenerationOperation,
        **kwargs
    ) -> bool:
        """Cancel video generation operation."""
        def _sync_cancel():
            try:
                # Get internal operation object
                internal_op = operation._operation_obj
                if not internal_op:
                    logger.warning("Operation object not found, cannot cancel")
                    return False
                
                # Try to cancel the operation
                internal_op.cancel()
                operation.status = "cancelled"
                logger.info(f"Video generation cancelled: {operation.operation_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to cancel operation: {e}")
                return False
        
        return await async_wrap(_sync_cancel)()
