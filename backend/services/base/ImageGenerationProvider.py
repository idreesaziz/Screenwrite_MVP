"""
Abstract base class for image generation providers.

This module defines the contract that all image generation provider implementations must follow.
It provides a consistent interface for different image generation services (Imagen, DALL-E, Stable Diffusion, etc.).
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ImageGenerationRequest:
    """
    Represents a request to generate images.
    
    Attributes:
        prompt: The text prompt that guides what images the model generates
        negative_prompt: Optional description of what to discourage in the generated images
        sample_count: Number of images to generate (default: 1)
        aspect_ratio: Aspect ratio for the generated images (e.g., "1:1", "16:9", "9:16")
        output_size: Output resolution (e.g., "1K", "2K")
        seed: Optional random seed for reproducible generation
        safety_filter_level: Safety filtering level (e.g., "block_medium_and_above")
        add_watermark: Whether to add an invisible watermark to generated images
        enhance_prompt: Use LLM-based prompt rewriting for better quality
        language: Language code for the prompt (e.g., "en", "ja", "zh")
        person_generation: Control generation of people ("dont_allow", "allow_adult", "allow_all")
        output_mime_type: Output format ("image/png" or "image/jpeg")
        compression_quality: JPEG compression quality (0-100)
        storage_uri: Optional Cloud Storage URI to store generated images
        metadata: Optional additional parameters
    """
    prompt: str
    negative_prompt: Optional[str] = None
    sample_count: int = 1
    aspect_ratio: Optional[str] = "1:1"
    output_size: Optional[str] = "1K"
    seed: Optional[int] = None
    safety_filter_level: Optional[str] = "block_medium_and_above"
    add_watermark: bool = True
    enhance_prompt: bool = True
    language: Optional[str] = "en"
    person_generation: Optional[str] = "allow_adult"
    output_mime_type: str = "image/png"
    compression_quality: Optional[int] = 75
    storage_uri: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class GeneratedImage:
    """
    Represents a single generated image.
    
    Attributes:
        image_bytes: Base64-encoded image bytes
        mime_type: Image MIME type (e.g., "image/png")
        enhanced_prompt: The enhanced prompt used (if prompt enhancement was enabled)
        storage_uri: Cloud Storage URI if image was saved to storage
        safety_attributes: Safety filtering attributes and scores
        rai_filtered_reason: Reason if image was filtered by responsible AI
        metadata: Additional image-specific metadata
    """
    image_bytes: str
    mime_type: str
    enhanced_prompt: Optional[str] = None
    storage_uri: Optional[str] = None
    safety_attributes: Optional[Dict[str, Any]] = None
    rai_filtered_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ImageGenerationResponse:
    """
    Represents a response from an image generation provider.
    
    Attributes:
        images: List of generated images
        model: The name/ID of the model that generated the images
        request_params: The original request parameters
        metadata: Optional additional response metadata
        timestamp: When the images were generated
    """
    images: List[GeneratedImage]
    model: str
    request_params: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ImageUpscaleRequest:
    """
    Represents a request to upscale an image.
    
    Attributes:
        image_bytes: Base64-encoded image bytes to upscale
        image_uri: Cloud Storage URI of image to upscale (alternative to image_bytes)
        upscale_factor: Upscaling factor ("x2" or "x4")
        output_mime_type: Output format ("image/png" or "image/jpeg")
        compression_quality: JPEG compression quality (0-100)
        storage_uri: Optional Cloud Storage URI to store upscaled image
        metadata: Optional additional parameters
    """
    image_bytes: Optional[str] = None
    image_uri: Optional[str] = None
    upscale_factor: str = "x2"
    output_mime_type: str = "image/png"
    compression_quality: Optional[int] = 75
    storage_uri: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ImageGenerationProvider(ABC):
    """
    Abstract base class for image generation providers.
    
    All image generation provider implementations (Imagen, DALL-E, Stable Diffusion, etc.) 
    must implement these methods to provide a consistent interface across different services.
    """
    
    @abstractmethod
    async def generate_images(
        self,
        request: ImageGenerationRequest,
        model_name: Optional[str] = None,
        **kwargs
    ) -> ImageGenerationResponse:
        """
        Generate images from a text prompt.
        
        Args:
            request: ImageGenerationRequest with prompt and generation parameters
            model_name: Override default model (None = use provider's default)
            **kwargs: Provider-specific parameters
            
        Returns:
            ImageGenerationResponse with generated images and metadata
            
        Raises:
            ValueError: If request is invalid or missing required fields
            RuntimeError: If API call fails
        """
        pass
    
    @abstractmethod
    async def upscale_image(
        self,
        request: ImageUpscaleRequest,
        model_name: Optional[str] = None,
        **kwargs
    ) -> GeneratedImage:
        """
        Upscale an existing image.
        
        Args:
            request: ImageUpscaleRequest with image and upscaling parameters
            model_name: Override default model (None = use provider's default)
            **kwargs: Provider-specific parameters
            
        Returns:
            GeneratedImage with upscaled image data
            
        Raises:
            ValueError: If request is invalid or missing required fields
            RuntimeError: If API call fails
        """
        pass
    
    @abstractmethod
    async def edit_image(
        self,
        image_bytes: str,
        prompt: str,
        mask_bytes: Optional[str] = None,
        model_name: Optional[str] = None,
        **kwargs
    ) -> ImageGenerationResponse:
        """
        Edit an existing image using a text prompt.
        
        Note: Not all providers support image editing. Implementation may raise NotImplementedError.
        
        Args:
            image_bytes: Base64-encoded image bytes to edit
            prompt: Text prompt describing the desired edit
            mask_bytes: Optional mask indicating which areas to edit
            model_name: Override default model (None = use provider's default)
            **kwargs: Provider-specific parameters
            
        Returns:
            ImageGenerationResponse with edited images and metadata
            
        Raises:
            NotImplementedError: If provider doesn't support image editing
            ValueError: If request is invalid
            RuntimeError: If API call fails
        """
        pass
