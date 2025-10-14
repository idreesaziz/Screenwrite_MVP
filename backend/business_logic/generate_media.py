"""
Business logic for AI-powered media generation (images and videos).

Handles:
- Image generation with Imagen (sync)
- Video generation with Veo (async with polling)
- Cloud storage upload
- Operation tracking for async video generation
"""

import logging
import uuid
import asyncio
from typing import Dict, Optional
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO

from services.base.ImageGenerationProvider import ImageGenerationProvider
from services.base.VideoGenerationProvider import (
    VideoGenerationProvider,
    VideoGenerationOperation
)
from services.base.StorageProvider import StorageProvider


logger = logging.getLogger(__name__)


class GeneratedAssetResult:
    """Result of a completed generation."""
    def __init__(
        self,
        asset_id: str,
        content_type: str,
        file_path: str,
        file_url: str,
        prompt: str,
        width: int,
        height: int,
        file_size: int,
        duration_seconds: Optional[float] = None
    ):
        self.asset_id = asset_id
        self.content_type = content_type
        self.file_path = file_path
        self.file_url = file_url
        self.prompt = prompt
        self.width = width
        self.height = height
        self.file_size = file_size
        self.duration_seconds = duration_seconds


class MediaGenerationService:
    """
    Service for generating images and videos with AI.
    
    Workflow:
    - Images: Generate → Upload to GCS → Return URL (sync)
    - Videos: Start generation → Return operation_id → Poll status → Download → Upload → Return URL
    """
    
    def __init__(
        self,
        image_provider: ImageGenerationProvider,
        video_provider: VideoGenerationProvider,
        storage_provider: StorageProvider
    ):
        """
        Initialize media generation service.
        
        Args:
            image_provider: Provider for image generation (Imagen)
            video_provider: Provider for video generation (Veo)
            storage_provider: Provider for cloud storage (GCS)
        """
        self.image_provider = image_provider
        self.video_provider = video_provider
        self.storage_provider = storage_provider
        
        # Track active video generation operations
        self.active_operations: Dict[str, Dict] = {}
        
        logger.info("MediaGenerationService initialized")
    
    async def generate_image(
        self,
        prompt: str,
        user_id: str,
        session_id: str,
        aspect_ratio: str = "16:9"
    ) -> GeneratedAssetResult:
        """
        Generate an image with Imagen and upload to storage.
        
        This is a synchronous operation - returns immediately with the image URL.
        
        Args:
            prompt: Text description of image to generate
            user_id: User ID for storage isolation
            session_id: Session ID for storage isolation
            aspect_ratio: Image aspect ratio ("16:9", "9:16")
            
        Returns:
            GeneratedAssetResult with image URL and metadata
            
        Raises:
            RuntimeError: If generation or upload fails
        """
        try:
            logger.info(f"Generating image for prompt: '{prompt[:50]}...'")
            
            # Step 1: Generate image with Imagen
            from services.base.ImageGenerationProvider import ImageGenerationRequest
            
            request = ImageGenerationRequest(
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                sample_count=1,
                enhance_prompt=True,
                output_mime_type="image/png"
            )
            
            response = await self.image_provider.generate_images(request)
            
            if not response.images:
                raise RuntimeError("No images generated")
            
            generated_image = response.images[0]
            logger.info(f"Image generated successfully with {len(generated_image.image_bytes)} bytes")
            
            # Step 2: Upload to cloud storage
            import base64
            image_bytes = base64.b64decode(generated_image.image_bytes)
            
            asset_id = str(uuid.uuid4())
            file_name = f"generated_image_{asset_id}.png"
            
            logger.info(f"Uploading image to storage: {file_name}")
            upload_result = await self.storage_provider.upload_file(
                file_data=BytesIO(image_bytes),
                user_id=user_id,
                session_id=session_id,
                filename=file_name,
                content_type="image/png"
            )
            
            logger.info(f"✅ Image generated and uploaded: {upload_result.url[:80]}...")
            
            # Step 3: Build result (extract dimensions from image if possible)
            from PIL import Image
            img = Image.open(BytesIO(image_bytes))
            width, height = img.size
            
            return GeneratedAssetResult(
                asset_id=asset_id,
                content_type="image",
                file_path=upload_result.path,
                file_url=upload_result.signed_url or upload_result.url,  # Use signed URL for secure browser access
                prompt=prompt,
                width=width,
                height=height,
                file_size=len(image_bytes)
            )
            
        except Exception as e:
            logger.error(f"Image generation failed: {e}", exc_info=True)
            raise RuntimeError(f"Image generation failed: {e}")
    
    async def generate_video(
        self,
        prompt: str,
        user_id: str,
        session_id: str,
        negative_prompt: Optional[str] = None,
        aspect_ratio: str = "16:9",
        resolution: str = "720p",
        reference_image_url: Optional[str] = None
    ) -> str:
        """
        Start async video generation with Veo.
        
        This returns immediately with an operation_id. Client must poll
        check_video_status() to get the final result.
        
        Args:
            prompt: Text description of video to generate
            user_id: User ID for storage isolation
            session_id: Session ID for storage isolation
            negative_prompt: What to avoid in generation
            aspect_ratio: Video aspect ratio ("16:9", "9:16")
            resolution: Video resolution ("720p", "1080p")
            reference_image_url: Optional reference image URL for image-to-video
            
        Returns:
            operation_id: String ID to poll for status
            
        Raises:
            RuntimeError: If generation fails to start
        """
        try:
            logger.info(f"Starting video generation for prompt: '{prompt[:50]}...'")
            
            # Download reference image if provided
            reference_image = None
            if reference_image_url:
                try:
                    logger.info(f"Downloading reference image: {reference_image_url[:80]}...")
                    response = requests.get(reference_image_url, timeout=10)
                    response.raise_for_status()
                    reference_image = Image.open(BytesIO(response.content))
                    logger.info(f"Reference image downloaded: {reference_image.size}")
                except Exception as img_error:
                    logger.warning(f"Failed to download reference image: {img_error}")
                    # Continue without reference image
            
            # Start video generation (async operation)
            operation = await self.video_provider.generate_video(
                prompt=prompt,
                negative_prompt=negative_prompt,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                reference_image=reference_image
            )
            
            # Store operation data for later retrieval
            self.active_operations[operation.operation_id] = {
                'operation': operation,
                'user_id': user_id,
                'session_id': session_id,
                'prompt': prompt,
                'resolution': resolution,
                'started_at': datetime.utcnow()
            }
            
            logger.info(f"✅ Video generation started: {operation.operation_id}")
            
            return operation.operation_id
            
        except Exception as e:
            logger.error(f"Video generation failed to start: {e}", exc_info=True)
            raise RuntimeError(f"Video generation failed to start: {e}")
    
    async def check_video_status(
        self,
        operation_id: str
    ) -> tuple[str, Optional[GeneratedAssetResult], Optional[str]]:
        """
        Check status of video generation operation.
        
        If completed, downloads video and uploads to storage.
        
        Args:
            operation_id: Operation ID from generate_video()
            
        Returns:
            Tuple of (status, result, error_message)
            - status: "processing", "completed", or "failed"
            - result: GeneratedAssetResult if completed, None otherwise
            - error_message: Error message if failed, None otherwise
            
        Raises:
            ValueError: If operation_id not found
        """
        if operation_id not in self.active_operations:
            raise ValueError(f"Operation not found: {operation_id}")
        
        operation_data = self.active_operations[operation_id]
        operation: VideoGenerationOperation = operation_data['operation']
        user_id = operation_data['user_id']
        session_id = operation_data['session_id']
        prompt = operation_data['prompt']
        resolution = operation_data['resolution']
        
        try:
            # Check current status
            logger.info(f"Checking status for operation: {operation_id}")
            updated_operation = await self.video_provider.check_generation_status(operation)
            
            # Update stored operation
            operation_data['operation'] = updated_operation
            
            if updated_operation.status == "failed":
                logger.error(f"Video generation failed: {updated_operation.error_message}")
                # Clean up operation
                del self.active_operations[operation_id]
                return ("failed", None, updated_operation.error_message)
            
            if updated_operation.status != "completed":
                logger.debug(f"Video still processing: {operation_id}")
                return ("processing", None, None)
            
            # Video is complete - download and upload to storage
            logger.info(f"Video generation completed, downloading: {operation_id}")
            
            # Download video
            generated_video = await self.video_provider.download_generated_video(
                operation=updated_operation
            )
            
            logger.info(f"Video downloaded: {generated_video.file_size} bytes")
            
            # Upload to storage
            asset_id = str(uuid.uuid4())
            file_name = f"generated_video_{asset_id}.mp4"
            
            logger.info(f"Uploading video to storage: {file_name}")
            upload_result = await self.storage_provider.upload_file(
                file_data=BytesIO(generated_video.video_data),
                user_id=user_id,
                session_id=session_id,
                filename=file_name,
                content_type="video/mp4"
            )
            
            logger.info(f"✅ Video uploaded: {upload_result.url[:80]}...")
            
            # Build result
            result = GeneratedAssetResult(
                asset_id=asset_id,
                content_type="video",
                file_path=upload_result.path,
                file_url=upload_result.signed_url or upload_result.url,  # Use signed URL for secure browser access
                prompt=prompt,
                width=generated_video.width,
                height=generated_video.height,
                file_size=generated_video.file_size,
                duration_seconds=generated_video.duration_seconds
            )
            
            # Clean up operation
            del self.active_operations[operation_id]
            
            return ("completed", result, None)
            
        except Exception as e:
            logger.error(f"Error checking video status: {e}", exc_info=True)
            # Don't delete operation on transient errors
            return ("failed", None, str(e))
