"""
Business logic for AI-powered media generation (images, videos, logos, and voice-overs).

Handles:
- Image generation with Imagen (sync)
- Video generation with Veo (async with polling)
- Logo generation with transparent backgrounds (sync)
- Voice-over generation with Google TTS (sync)
- Cloud storage upload
- Operation tracking for async video generation
"""

import logging
import uuid
import asyncio
from typing import Dict, Optional
from datetime import datetime
from PIL import Image
import httpx
from io import BytesIO
from rembg import remove, new_session

from services.base.ImageGenerationProvider import ImageGenerationProvider
from services.base.VideoGenerationProvider import (
    VideoGenerationProvider,
    VideoGenerationOperation
)
from services.base.VoiceGenerationProvider import (
    VoiceGenerationProvider,
    VoiceGenerationRequest
)
from services.base.StorageProvider import StorageProvider


logger = logging.getLogger(__name__)


class GeneratedAssetResult:
    """Result of a completed generation."""
    def __init__(
        self,
        asset_id: str,
        name: str,
        content_type: str,
        file_path: str,
        file_url: str,
        gcs_uri: str,
        prompt: str,
        width: int,
        height: int,
        file_size: int,
        duration_seconds: Optional[float] = None
    ):
        self.asset_id = asset_id
        self.name = name
        self.content_type = content_type
        self.file_path = file_path
        self.file_url = file_url
        self.gcs_uri = gcs_uri
        self.prompt = prompt
        self.width = width
        self.height = height
        self.file_size = file_size
        self.duration_seconds = duration_seconds


class MediaGenerationService:
    """
    Service for generating images, videos, logos, and voice-overs with AI.
    
    Workflow:
    - Images: Generate → Upload to GCS → Return URL (sync)
    - Videos: Start generation → Return operation_id → Poll status → Download → Upload → Return URL
    - Logos: Generate → Remove background → Auto-crop → Upload → Return URL (sync)
    - Voice-overs: Generate → Upload to GCS → Return URL + duration (sync)
    """
    
    def __init__(
        self,
        image_provider: ImageGenerationProvider,
        video_provider: VideoGenerationProvider,
        voice_provider: VoiceGenerationProvider,
        storage_provider: StorageProvider
    ):
        """
        Initialize media generation service.
        
        Args:
            image_provider: Provider for image generation (Imagen)
            video_provider: Provider for video generation (Veo)
            voice_provider: Provider for voice/speech generation (Google TTS)
            storage_provider: Provider for cloud storage (GCS)
        """
        self.image_provider = image_provider
        self.video_provider = video_provider
        self.voice_provider = voice_provider
        self.storage_provider = storage_provider
        
        # Track active video generation operations
        self.active_operations: Dict[str, Dict] = {}
        
        logger.info("MediaGenerationService initialized")
    
    async def generate_image(
        self,
        prompt: str,
        user_id: str,
        session_id: str,
        aspect_ratio: str = "16:9",
        suggested_name: str = ""
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
            
            # Step 2: Get existing names for collision checking
            existing_names = await self.storage_provider.get_existing_names(user_id, session_id)
            
            # Step 3: Generate unique name
            from utils.naming import create_generated_name, generate_unique_name
            asset_id = str(uuid.uuid4())
            base_name = create_generated_name(suggested_name, "image", asset_id[:6])
            unique_name = generate_unique_name(base_name, existing_names)
            
            # Step 4: Upload to cloud storage
            import base64
            image_bytes = base64.b64decode(generated_image.image_bytes)
            
            file_name = f"generated_image_{asset_id}.png"
            
            logger.info(f"Uploading image to storage: {unique_name}")
            upload_result = await self.storage_provider.upload_file(
                file_data=BytesIO(image_bytes),
                user_id=user_id,
                session_id=session_id,
                filename=file_name,
                name=unique_name,
                content_type="image/png"
            )
            
            logger.info(f"✅ Image generated and uploaded: {unique_name}")
            
            # Step 5: Build result
            from PIL import Image
            img = Image.open(BytesIO(image_bytes))
            width, height = img.size
            
            # Build GCS URI for Vertex AI access
            bucket_name = self.storage_provider.bucket_name if hasattr(self.storage_provider, 'bucket_name') else "screenwrite-media"
            gcs_uri = f"gs://{bucket_name}/{upload_result.path}"
            
            return GeneratedAssetResult(
                asset_id=asset_id,
                name=unique_name,
                content_type="image",
                file_path=upload_result.path,
                file_url=upload_result.signed_url or upload_result.url,
                gcs_uri=gcs_uri,
                prompt=prompt,
                width=width,
                height=height,
                file_size=len(image_bytes)
            )
            
        except Exception as e:
            logger.error(f"Image generation failed: {e}", exc_info=True)
            raise RuntimeError(f"Image generation failed: {e}")
    
    async def generate_logo(
        self,
        prompt: str,
        user_id: str,
        session_id: str,
        suggested_name: str = ""
    ) -> GeneratedAssetResult:
        """
        Generate a logo with transparent background.
        
        Process:
        1. Enhance user's simple prompt with system instructions for green background
        2. Generate image with provider
        3. Remove green background to create transparent PNG
        4. Upload to storage
        
        Args:
            prompt: Simple user description (e.g., "coffee cup minimalistic", "flower cartoon")
            user_id: User ID for storage isolation
            session_id: Session ID for storage isolation
            
        Returns:
            GeneratedAssetResult with transparent PNG URL and metadata
            
        Raises:
            RuntimeError: If generation or processing fails
        """
        try:
            logger.info(f"Generating logo for prompt: '{prompt}'")
            
            # Step 1: Build enhanced prompt with system instructions
            # Note: Request solid background to help ML model separate logo from background
            system_instructions = """Professional logo design requirements:

BACKGROUND: Solid, uniform, consistent color background (any color) - no gradients, textures, or patterns

DESIGN: Crisp clean edges, clear boundaries, professional appearance, scalable design, high contrast with background

POSITIONING: Logo centered, well-defined separation from background

COMPOSITION: Logo only, professional quality, appropriate for branding and overlays

Generate logo: """
            
            enhanced_prompt = system_instructions + prompt
            logger.info(f"Enhanced logo prompt length: {len(enhanced_prompt)} characters")
            
            # Step 2: Generate image with provider
            from services.base.ImageGenerationProvider import ImageGenerationRequest
            
            request = ImageGenerationRequest(
                prompt=enhanced_prompt,
                aspect_ratio="1:1",  # Logos are typically square
                sample_count=1,
                enhance_prompt=False,  # Don't enhance, we've already added instructions
                output_mime_type="image/png"
            )
            
            response = await self.image_provider.generate_images(request)
            
            if not response.images:
                logger.error("No logo image generated in response")
                raise RuntimeError("No logo image generated")
            
            generated_image = response.images[0]
            logger.info(f"Logo image generated successfully with {len(generated_image.image_bytes)} bytes")
            
            # Step 3: Decode image and remove background using rembg
            import base64
            
            logger.info("Decoding image bytes...")
            image_bytes = base64.b64decode(generated_image.image_bytes)
            logger.info(f"Decoded {len(image_bytes)} bytes")
            
            img = Image.open(BytesIO(image_bytes))
            logger.info(f"Opened image: {img.size}, mode: {img.mode}")
            
            # Remove background using rembg ML model
            logger.info("Removing background with rembg...")
            result_img = remove(img)
            logger.info(f"Background removed successfully. Output mode: {result_img.mode}")
            
            # Auto-crop to remove excess transparent space while maintaining square aspect ratio
            logger.info("Auto-cropping logo to remove excess padding...")
            
            # Get alpha channel and find bounding box of non-transparent pixels
            alpha = result_img.split()[-1]
            bbox = alpha.getbbox()
            
            if bbox:
                # Calculate dimensions of logo content
                logo_width = bbox[2] - bbox[0]
                logo_height = bbox[3] - bbox[1]
                
                # Use larger dimension to maintain square aspect ratio
                square_size = max(logo_width, logo_height)
                
                # Add 10% padding on each side (20% total)
                padding_percent = 0.10
                padding = int(square_size * padding_percent)
                final_size = square_size + (padding * 2)
                
                # Calculate center point of logo
                center_x = (bbox[0] + bbox[2]) / 2
                center_y = (bbox[1] + bbox[3]) / 2
                
                # Calculate crop coordinates (centered square)
                left = int(center_x - (final_size / 2))
                top = int(center_y - (final_size / 2))
                right = int(left + final_size)
                bottom = int(top + final_size)
                
                # Ensure crop is within image bounds
                img_width, img_height = result_img.size
                left = max(0, left)
                top = max(0, top)
                right = min(img_width, right)
                bottom = min(img_height, bottom)
                
                # Crop the image
                result_img = result_img.crop((left, top, right, bottom))
                logger.info(f"Logo cropped from {img.size} to {result_img.size} (removed excess padding)")
            else:
                logger.warning("No visible logo content found, skipping auto-crop")
            
            # Save to bytes buffer as PNG with transparency
            output_buffer = BytesIO()
            result_img.save(output_buffer, format='PNG', optimize=True)
            transparent_png_bytes = output_buffer.getvalue()
            
            logger.info(f"Transparent PNG created. Size: {len(transparent_png_bytes)} bytes")
            
            # Step 4: Get existing names and generate unique name
            existing_names = await self.storage_provider.get_existing_names(user_id, session_id)
            from utils.naming import create_generated_name, generate_unique_name
            asset_id = str(uuid.uuid4())
            base_name = create_generated_name(suggested_name, "logo", asset_id[:6])
            unique_name = generate_unique_name(base_name, existing_names)
            
            # Step 5: Upload to cloud storage
            file_name = f"generated_logo_{asset_id}.png"
            
            logger.info(f"Uploading logo to storage: {unique_name}")
            upload_result = await self.storage_provider.upload_file(
                file_data=BytesIO(transparent_png_bytes),
                user_id=user_id,
                session_id=session_id,
                filename=file_name,
                name=unique_name,
                content_type="image/png"
            )
            
            logger.info(f"✅ Logo generated and uploaded: {unique_name}")
            
            # Step 6: Build result with dimensions
            width, height = result_img.size
            
            # Build GCS URI for Vertex AI access
            bucket_name = self.storage_provider.bucket_name if hasattr(self.storage_provider, 'bucket_name') else "screenwrite-media"
            gcs_uri = f"gs://{bucket_name}/{upload_result.path}"
            
            return GeneratedAssetResult(
                asset_id=asset_id,
                name=unique_name,
                content_type="logo",
                file_path=upload_result.path,
                file_url=upload_result.signed_url or upload_result.url,
                gcs_uri=gcs_uri,
                prompt=prompt,  # Return original user prompt, not enhanced
                width=width,
                height=height,
                file_size=len(transparent_png_bytes)
            )
            
        except Exception as e:
            logger.error(f"Logo generation failed: {e}", exc_info=True)
            raise RuntimeError(f"Logo generation failed: {e}")
    
    async def generate_video(
        self,
        prompt: str,
        user_id: str,
        session_id: str,
        negative_prompt: Optional[str] = None,
        aspect_ratio: str = "16:9",
        resolution: str = "720p",
        reference_image_url: Optional[str] = None,
        suggested_name: str = ""
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
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.get(reference_image_url)
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
                reference_image=reference_image,
                user_id=user_id,
                session_id=session_id
            )
            
            # Store operation data for later retrieval
            self.active_operations[operation.operation_id] = {
                'operation': operation,
                'user_id': user_id,
                'session_id': session_id,
                'prompt': prompt,
                'resolution': resolution,
                'suggested_name': suggested_name,
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
            
            # Get existing names and generate unique name
            existing_names = await self.storage_provider.get_existing_names(user_id, session_id)
            from utils.naming import create_generated_name, generate_unique_name
            asset_id = str(uuid.uuid4())
            suggested_name = operation_data.get('suggested_name', '')
            base_name = create_generated_name(suggested_name, "video", asset_id[:6])
            unique_name = generate_unique_name(base_name, existing_names)
            
            # Upload to storage
            file_name = f"generated_video_{asset_id}.mp4"
            
            logger.info(f"Uploading video to storage: {unique_name}")
            upload_result = await self.storage_provider.upload_file(
                file_data=BytesIO(generated_video.video_data),
                user_id=user_id,
                session_id=session_id,
                filename=file_name,
                name=unique_name,
                content_type="video/mp4"
            )
            
            logger.info(f"✅ Video uploaded: {unique_name}")
            
            # Build GCS URI for Vertex AI access
            bucket_name = self.storage_provider.bucket_name if hasattr(self.storage_provider, 'bucket_name') else "screenwrite-media"
            gcs_uri = f"gs://{bucket_name}/{upload_result.path}"
            
            # Build result
            result = GeneratedAssetResult(
                asset_id=asset_id,
                name=unique_name,
                content_type="video",
                file_path=upload_result.path,
                file_url=upload_result.signed_url or upload_result.url,
                gcs_uri=gcs_uri,
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
    
    async def generate_voice(
        self,
        text: str,
        user_id: str,
        session_id: str,
        voice_id: str = "Aoede",
        language_code: str = "en-US",
        style_prompt: Optional[str] = None,
        speaking_rate: float = 1.0,
        pitch: float = 0.0,
        suggested_name: str = ""
    ) -> GeneratedAssetResult:
        """
        Generate voice-over/speech from text script using Gemini 2.5 Pro TTS.
        
        Workflow:
        1. Generate audio via Gemini TTS with prompt-based style control
        2. Upload to cloud storage
        3. Return URL with duration metadata (critical for timeline placement)
        
        Args:
            text: Script text to convert to speech
            user_id: User ID for storage isolation
            session_id: Session ID for storage isolation
            voice_id: Gemini voice name (e.g., "Aoede", "Charon", "Kore")
            language_code: BCP-47 language code (e.g., "en-US")
            style_prompt: Optional delivery style (e.g., "Speak dramatically with urgency", "[whispering]")
                          If None, uses natural conversational tone
            speaking_rate: Speech speed (0.25-4.0, default 1.0)
            pitch: Voice pitch (-20.0 to 20.0, default 0.0)
            
        Returns:
            GeneratedAssetResult with audio URL and duration
            
        Raises:
            RuntimeError: If voice generation or upload fails
        """
        try:
            logger.info(f"Generating voice-over: {len(text)} characters, voice={voice_id}")
            
            # Step 1: Generate audio via TTS provider
            request = VoiceGenerationRequest(
                text=text,
                voice_id=voice_id,
                language_code=language_code,
                style_prompt=style_prompt,
                speaking_rate=speaking_rate,
                pitch=pitch,
                audio_encoding="MP3",
                sample_rate_hertz=24000
            )
            
            result = await self.voice_provider.generate_voice(request)
            logger.info(f"Voice generated: {result.duration_seconds:.2f}s, {len(result.audio_bytes)} bytes")
            
            # Step 2: Get existing names and generate unique name
            existing_names = await self.storage_provider.get_existing_names(user_id, session_id)
            from utils.naming import create_generated_name, generate_unique_name
            asset_id = str(uuid.uuid4())
            base_name = create_generated_name(suggested_name, "audio", asset_id[:6])
            unique_name = generate_unique_name(base_name, existing_names)
            
            # Step 3: Upload to cloud storage
            file_name = f"voiceover_{asset_id}.mp3"
            
            logger.info(f"Uploading voice-over to storage: {unique_name}")
            upload_result = await self.storage_provider.upload_file(
                file_data=BytesIO(result.audio_bytes),
                user_id=user_id,
                session_id=session_id,
                filename=file_name,
                name=unique_name,
                content_type="audio/mpeg"
            )
            
            logger.info(f"✅ Voice-over generated and uploaded: {unique_name}")
            
            # Step 4: Build result with duration
            bucket_name = self.storage_provider.bucket_name if hasattr(self.storage_provider, 'bucket_name') else "screenwrite-media"
            gcs_uri = f"gs://{bucket_name}/{upload_result.path}"
            
            return GeneratedAssetResult(
                asset_id=asset_id,
                name=unique_name,
                content_type="audio",
                file_path=upload_result.path,
                file_url=upload_result.signed_url or upload_result.url,
                gcs_uri=gcs_uri,
                prompt=text,
                width=0,
                height=0,
                file_size=len(result.audio_bytes),
                duration_seconds=result.duration_seconds  # Essential for timeline!
            )
            
        except Exception as e:
            logger.error(f"Voice generation failed: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate voice-over: {str(e)}")
