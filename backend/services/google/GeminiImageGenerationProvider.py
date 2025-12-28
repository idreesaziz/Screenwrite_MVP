"""Google Gemini 3 Pro Image generation provider using Vertex AI Gen AI SDK.

This provider uses the Gemini 3 Pro Image model for high-quality image generation,
particularly suited for logos and text rendering.
"""

import asyncio
import base64
import logging
import os
from typing import Optional, Dict, Any

from google import genai
from google.genai import types

from services.base.ImageGenerationProvider import (
    ImageGenerationProvider,
    ImageGenerationRequest,
    ImageGenerationResponse,
    GeneratedImage,
    ImageUpscaleRequest
)

logger = logging.getLogger(__name__)


class GeminiImageGenerationProvider(ImageGenerationProvider):
    """Gemini 3 Pro Image provider using Vertex AI Gen AI SDK.
    
    Optimized for:
    - Logo generation with accurate text rendering
    - High-quality image generation up to 4K
    - Complex multi-turn image editing
    
    Authentication is handled via Application Default Credentials (ADC).
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        location: str = "global",
        default_model_name: str = "gemini-3-pro-image-preview",
    ):
        """
        Initialize Gemini Image Generation provider.
        
        Args:
            project_id: Google Cloud project ID
            location: Must be "global" for Gemini 3 models
            default_model_name: Default model (gemini-3-pro-image-preview)
        """
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT')
        self.location = location
        self.default_model_name = default_model_name
        
        # Create client for Vertex AI
        self.client = genai.Client(
            vertexai=True,
            project=self.project_id,
            location=self.location
        )
        
        logger.info(
            f"Initialized GeminiImageGenerationProvider with model: {default_model_name}, "
            f"project: {self.project_id}, location: {location}"
        )
    
    def _map_aspect_ratio(self, aspect_ratio: Optional[str]) -> str:
        """Map aspect ratio to Gemini-supported format.
        
        Supported: 1:1, 3:2, 2:3, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9
        """
        valid_ratios = {"1:1", "3:2", "2:3", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"}
        if aspect_ratio in valid_ratios:
            return aspect_ratio
        # Default to 1:1 for unsupported ratios
        return "1:1"
    
    def _map_image_size(self, output_size: Optional[str]) -> str:
        """Map output size to Gemini format.
        
        Supported: 1K, 2K, 4K
        """
        valid_sizes = {"1K", "2K", "4K"}
        if output_size and output_size.upper() in valid_sizes:
            return output_size.upper()
        return "1K"
    
    async def generate_images(
        self,
        request: ImageGenerationRequest,
        model_name: Optional[str] = None,
        **kwargs
    ) -> ImageGenerationResponse:
        """
        Generate images using Gemini 3 Pro Image.
        
        Args:
            request: ImageGenerationRequest with prompt and generation parameters
            model_name: Override default model
            **kwargs: Additional parameters
            
        Returns:
            ImageGenerationResponse with generated images
        """
        if not request.prompt:
            raise ValueError("Prompt is required")
        
        model = model_name or self.default_model_name
        aspect_ratio = self._map_aspect_ratio(request.aspect_ratio)
        image_size = self._map_image_size(request.output_size)
        
        logger.info(f"Generating image with Gemini: model={model}, aspect_ratio={aspect_ratio}, size={image_size}")
        logger.debug(f"Prompt: {request.prompt[:200]}...")
        
        try:
            # Build config
            config = types.GenerateContentConfig(
                response_modalities=['IMAGE'],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                    image_size=image_size,
                ),
            )
            
            # Generate image (sync call wrapped in asyncio.to_thread)
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=model,
                contents=request.prompt,
                config=config
            )
            
            # Check for errors
            if not response.candidates:
                raise RuntimeError("No candidates in response")
            
            candidate = response.candidates[0]
            if candidate.finish_reason and candidate.finish_reason != types.FinishReason.STOP:
                reason = candidate.finish_reason
                logger.error(f"Generation failed with reason: {reason}")
                raise RuntimeError(f"Image generation failed: {reason}")
            
            # Extract images from response
            images = []
            for part in candidate.content.parts:
                if part.inline_data:
                    # inline_data.data is already base64 encoded bytes
                    image_data = part.inline_data.data
                    
                    # Ensure it's base64 string
                    if isinstance(image_data, bytes):
                        image_b64 = base64.b64encode(image_data).decode('utf-8')
                    else:
                        image_b64 = image_data
                    
                    mime_type = part.inline_data.mime_type or "image/png"
                    
                    images.append(GeneratedImage(
                        image_bytes=image_b64,
                        mime_type=mime_type,
                        enhanced_prompt=None,
                        metadata={"model": model}
                    ))
            
            if not images:
                raise RuntimeError("No images generated in response")
            
            logger.info(f"Successfully generated {len(images)} image(s)")
            
            return ImageGenerationResponse(
                images=images,
                model=model,
                request_params={
                    "prompt": request.prompt,
                    "aspect_ratio": aspect_ratio,
                    "image_size": image_size,
                },
                metadata={"provider": "gemini"}
            )
            
        except Exception as e:
            logger.error(f"Gemini image generation failed: {e}", exc_info=True)
            raise RuntimeError(f"Gemini image generation failed: {e}")
    
    async def upscale_image(
        self,
        request: ImageUpscaleRequest,
        model_name: Optional[str] = None,
        **kwargs
    ) -> ImageGenerationResponse:
        """
        Upscale an image. Not directly supported by Gemini - use Imagen for upscaling.
        
        Raises:
            NotImplementedError: Gemini does not support direct upscaling
        """
        raise NotImplementedError(
            "Image upscaling is not supported by Gemini. Use ImagenGenerationProvider for upscaling."
        )
    
    async def edit_image(
        self,
        image_bytes: str,
        prompt: str,
        mask_bytes: Optional[str] = None,
        model_name: Optional[str] = None,
        **kwargs
    ) -> ImageGenerationResponse:
        """
        Edit an existing image with a prompt.
        
        Args:
            image_bytes: Base64-encoded source image
            prompt: Edit instructions
            mask_bytes: Optional mask (not used by Gemini)
            model_name: Override default model
            
        Returns:
            ImageGenerationResponse with edited image
        """
        model = model_name or self.default_model_name
        
        logger.info(f"Editing image with Gemini: model={model}")
        
        try:
            # Decode image bytes
            if isinstance(image_bytes, str):
                image_data = base64.b64decode(image_bytes)
            else:
                image_data = image_bytes
            
            # Build content with image and prompt
            contents = [
                types.Part.from_bytes(
                    data=image_data,
                    mime_type="image/png",
                ),
                prompt,
            ]
            
            config = types.GenerateContentConfig(
                response_modalities=['IMAGE', 'TEXT'],
                image_config=types.ImageConfig(
                    image_size="1K",
                ),
            )
            
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=model,
                contents=contents,
                config=config
            )
            
            # Extract images
            images = []
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    image_data = part.inline_data.data
                    if isinstance(image_data, bytes):
                        image_b64 = base64.b64encode(image_data).decode('utf-8')
                    else:
                        image_b64 = image_data
                    
                    images.append(GeneratedImage(
                        image_bytes=image_b64,
                        mime_type=part.inline_data.mime_type or "image/png",
                        metadata={"model": model, "operation": "edit"}
                    ))
            
            if not images:
                raise RuntimeError("No edited images in response")
            
            return ImageGenerationResponse(
                images=images,
                model=model,
                request_params={"prompt": prompt},
                metadata={"provider": "gemini", "operation": "edit"}
            )
            
        except Exception as e:
            logger.error(f"Gemini image editing failed: {e}", exc_info=True)
            raise RuntimeError(f"Gemini image editing failed: {e}")
