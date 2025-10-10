"""Google Imagen implementation using Vertex AI."""

import json
import logging
import os
from typing import List, Dict, Any, Optional
import requests
from google.cloud import aiplatform
from google.auth import default
from google.auth.transport.requests import Request

from services.base.ImageGenerationProvider import (
    ImageGenerationProvider,
    ImageGenerationRequest,
    ImageGenerationResponse,
    GeneratedImage,
    ImageUpscaleRequest
)

logger = logging.getLogger(__name__)


class ImagenProvider(ImageGenerationProvider):
    """Imagen implementation using Vertex AI (Google Cloud Platform).
    
    Supports Imagen 4.0, 3.0, and 2.0 models for image generation and upscaling.
    
    Authentication is handled via Application Default Credentials (ADC):
    - Service account JSON file via GOOGLE_APPLICATION_CREDENTIALS env var
    - gcloud auth application-default login
    - Workload Identity (for GKE/Cloud Run)
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        location: str = "us-central1",
        default_model_name: str = "imagen-4.0-generate-001",
    ):
        """
        Initialize Vertex AI Imagen provider using Application Default Credentials.
        
        Args:
            project_id: Google Cloud project ID (optional, will use from ADC if not provided)
            location: GCP region (default: us-central1)
            default_model_name: Default Imagen model to use
        
        Available models:
            - imagen-4.0-generate-001 (latest, best quality)
            - imagen-4.0-fast-generate-001 (faster generation)
            - imagen-4.0-ultra-generate-001 (highest quality)
            - imagen-3.0-generate-002
            - imagen-3.0-fast-generate-001
            - imagegeneration@006 (Imagen 2, deprecated)
        
        Authentication:
            Uses Application Default Credentials (ADC) in this order:
            1. GOOGLE_APPLICATION_CREDENTIALS environment variable pointing to service account JSON
            2. gcloud auth application-default login credentials
            3. Workload Identity (in GKE/Cloud Run)
        """
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT')
        self.location = location
        self.default_model_name = default_model_name
        
        # Initialize Vertex AI
        aiplatform.init(project=self.project_id, location=self.location)
        
        # Get credentials for API calls with correct scopes
        self.credentials, _ = default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
        if not self.credentials.valid:
            self.credentials.refresh(Request())
        
        logger.info(f"Initialized Imagen with model: {default_model_name}, project: {self.project_id}, location: {location}")
    
    def _get_endpoint_url(self, model_name: str) -> str:
        """Construct the Vertex AI endpoint URL for Imagen."""
        return (
            f"https://{self.location}-aiplatform.googleapis.com/v1/"
            f"projects/{self.project_id}/locations/{self.location}/"
            f"publishers/google/models/{model_name}:predict"
        )
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers with access token."""
        if not self.credentials.valid:
            self.credentials.refresh(Request())
        
        return {
            "Authorization": f"Bearer {self.credentials.token}",
            "Content-Type": "application/json; charset=utf-8"
        }
    
    async def generate_images(
        self,
        request: ImageGenerationRequest,
        model_name: Optional[str] = None,
        **kwargs
    ) -> ImageGenerationResponse:
        """
        Generate images using Imagen.
        
        Args:
            request: ImageGenerationRequest with prompt and generation parameters
            model_name: Override default model
            **kwargs: Additional provider-specific parameters
            
        Returns:
            ImageGenerationResponse with generated images
        """
        if not request.prompt:
            raise ValueError("Prompt is required")
        
        model = model_name or self.default_model_name
        
        # Build request payload
        payload = {
            "instances": [
                {
                    "prompt": request.prompt
                }
            ],
            "parameters": {
                "sampleCount": request.sample_count,
            }
        }
        
        # Add optional parameters
        if request.negative_prompt and "imagen-3" not in model and "imagen-4" not in model:
            # negativePrompt not supported in Imagen 3+
            payload["instances"][0]["negativePrompt"] = request.negative_prompt
        
        if request.aspect_ratio:
            payload["parameters"]["aspectRatio"] = request.aspect_ratio
        
        if request.output_size:
            payload["parameters"]["sampleImageSize"] = request.output_size
        
        if request.seed is not None:
            payload["parameters"]["seed"] = request.seed
        
        if request.safety_filter_level:
            payload["parameters"]["safetySetting"] = request.safety_filter_level
        
        if not request.add_watermark:
            payload["parameters"]["addWatermark"] = False
        
        if not request.enhance_prompt:
            payload["parameters"]["enhancePrompt"] = False
        
        if request.language and request.language != "en":
            payload["parameters"]["language"] = request.language
        
        if request.person_generation:
            payload["parameters"]["personGeneration"] = request.person_generation
        
        # Output options
        output_options = {}
        if request.output_mime_type:
            output_options["mimeType"] = request.output_mime_type
        if request.output_mime_type == "image/jpeg" and request.compression_quality:
            output_options["compressionQuality"] = request.compression_quality
        
        if output_options:
            payload["parameters"]["outputOptions"] = output_options
        
        if request.storage_uri:
            payload["parameters"]["storageUri"] = request.storage_uri
        
        # Merge additional kwargs
        payload["parameters"].update(kwargs)
        
        # Make API request
        endpoint_url = self._get_endpoint_url(model)
        headers = self._get_auth_headers()
        
        logger.info(f"Generating {request.sample_count} images with model: {model}")
        
        response = requests.post(endpoint_url, headers=headers, json=payload)
        
        if response.status_code != 200:
            error_msg = f"Imagen API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        response_data = response.json()
        
        # Parse response
        images = []
        for prediction in response_data.get("predictions", []):
            img = GeneratedImage(
                image_bytes=prediction.get("bytesBase64Encoded", ""),
                mime_type=prediction.get("mimeType", request.output_mime_type),
                enhanced_prompt=prediction.get("prompt"),
                storage_uri=prediction.get("storageUri"),
                safety_attributes=prediction.get("safetyAttributes"),
                rai_filtered_reason=prediction.get("raiFilteredReason"),
                metadata=prediction
            )
            images.append(img)
        
        return ImageGenerationResponse(
            images=images,
            model=model,
            request_params=payload["parameters"],
            metadata=response_data
        )
    
    async def upscale_image(
        self,
        request: ImageUpscaleRequest,
        model_name: Optional[str] = None,
        **kwargs
    ) -> GeneratedImage:
        """
        Upscale an image using Imagen.
        
        Args:
            request: ImageUpscaleRequest with image and upscaling parameters
            model_name: Override default model (must support upscaling)
            **kwargs: Additional provider-specific parameters
            
        Returns:
            GeneratedImage with upscaled image
        """
        if not request.image_bytes and not request.image_uri:
            raise ValueError("Either image_bytes or image_uri must be provided")
        
        # Upscaling is only supported by imagegeneration@002 and older models
        model = model_name or "imagegeneration@002"
        
        # Build request payload
        image_data = {}
        if request.image_bytes:
            image_data["bytesBase64Encoded"] = request.image_bytes
        elif request.image_uri:
            image_data["gcsUri"] = request.image_uri
        
        payload = {
            "instances": [
                {
                    "prompt": "",  # Required but empty for upscaling
                    "image": image_data
                }
            ],
            "parameters": {
                "sampleCount": 1,
                "mode": "upscale",
                "upscaleConfig": {
                    "upscaleFactor": request.upscale_factor
                }
            }
        }
        
        # Output options
        output_options = {}
        if request.output_mime_type:
            output_options["mimeType"] = request.output_mime_type
        if request.output_mime_type == "image/jpeg" and request.compression_quality:
            output_options["compressionQuality"] = request.compression_quality
        
        if output_options:
            payload["parameters"]["outputOptions"] = output_options
        
        if request.storage_uri:
            payload["parameters"]["storageUri"] = request.storage_uri
        
        # Merge additional kwargs
        payload["parameters"].update(kwargs)
        
        # Make API request
        endpoint_url = self._get_endpoint_url(model)
        headers = self._get_auth_headers()
        
        logger.info(f"Upscaling image by {request.upscale_factor} with model: {model}")
        
        response = requests.post(endpoint_url, headers=headers, json=payload)
        
        if response.status_code != 200:
            error_msg = f"Imagen API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        response_data = response.json()
        
        # Parse response (should be single image)
        prediction = response_data["predictions"][0]
        
        return GeneratedImage(
            image_bytes=prediction.get("bytesBase64Encoded", ""),
            mime_type=prediction.get("mimeType", request.output_mime_type),
            storage_uri=prediction.get("storageUri"),
            safety_attributes=prediction.get("safetyAttributes"),
            rai_filtered_reason=prediction.get("raiFilteredReason"),
            metadata=prediction
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
        Edit an image using Imagen.
        
        Note: Image editing/inpainting is not currently supported by Imagen API.
        This method raises NotImplementedError.
        
        Args:
            image_bytes: Base64-encoded image bytes to edit
            prompt: Text prompt describing the desired edit
            mask_bytes: Optional mask indicating which areas to edit
            model_name: Override default model
            **kwargs: Additional parameters
            
        Raises:
            NotImplementedError: Imagen doesn't currently support image editing
        """
        raise NotImplementedError(
            "Image editing is not currently supported by the Imagen API. "
            "Only image generation and upscaling are available."
        )
