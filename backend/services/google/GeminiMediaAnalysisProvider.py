"""
Google Gemini implementation of MediaAnalysisProvider using Vertex AI.

Supports multimodal analysis of images, videos, audio, and documents using
Gemini's vision and multimodal capabilities.

Follows the official Vertex AI pattern with Gen AI SDK:
- Set GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION env vars
- Set GOOGLE_GENAI_USE_VERTEXAI=True to enable Vertex AI mode
- Uses Application Default Credentials (ADC) automatically

Authentication is handled via Application Default Credentials (ADC):
- Service account JSON file via GOOGLE_APPLICATION_CREDENTIALS env var
- gcloud auth application-default login
- Workload Identity (for GKE/Cloud Run)
"""

import os
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse
from google import genai
from google.genai.types import HttpOptions, Part, GenerationConfig

from ..base.MediaAnalysisProvider import MediaAnalysisProvider, MediaAnalysisResult

logger = logging.getLogger(__name__)


class GeminiMediaAnalysisProvider(MediaAnalysisProvider):
    """
    Gemini implementation for multimodal media analysis using Vertex AI.
    
    Supports:
    - Images (JPEG, PNG, WebP, GIF, etc.)
    - Videos (MP4, MOV, AVI, etc.) up to 1-2 hours
    - Audio (MP3, WAV, AAC, etc.)
    - Documents (PDF, TXT, etc.)
    
    File sources:
    - GCS URIs (gs://bucket/path) - recommended for Vertex AI
    - HTTP/HTTPS URLs (signed URLs, public URLs)
    
    Note: Uses Part.from_uri() pattern from official Vertex AI docs.
    
    Authentication:
        Requires environment variables:
        - GOOGLE_CLOUD_PROJECT: Your GCP project ID
        - GOOGLE_CLOUD_LOCATION: Region (e.g., us-central1, global)
        - GOOGLE_GENAI_USE_VERTEXAI: Set to "True" to enable Vertex AI mode
        
        Uses Application Default Credentials (ADC) in this order:
        1. GOOGLE_APPLICATION_CREDENTIALS environment variable pointing to service account JSON
        2. gcloud auth application-default login credentials
        3. Workload Identity (in GKE/Cloud Run)
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        location: str = "us-central1",
        default_model: str = "gemini-2.0-flash-exp"
    ):
        """
        Initialize Gemini media analysis provider using Vertex AI.
        
        Args:
            project_id: GCP project ID (optional, uses GOOGLE_CLOUD_PROJECT env var if not provided)
            location: GCP region (default: us-central1)
            default_model: Default model to use for analysis
        
        Environment Variables Required:
            - GOOGLE_CLOUD_PROJECT: Your GCP project ID
            - GOOGLE_CLOUD_LOCATION: Region (default: us-central1)
            - GOOGLE_GENAI_USE_VERTEXAI: Set to "True"
            - GOOGLE_APPLICATION_CREDENTIALS: Path to service account JSON (for ADC)
        """
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT')
        self.location = location or os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
        self.default_model = default_model
        
        # Ensure Vertex AI mode is enabled
        if os.getenv('GOOGLE_GENAI_USE_VERTEXAI') != 'True':
            logger.warning("GOOGLE_GENAI_USE_VERTEXAI not set to 'True'. Setting it now.")
            os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'True'
        
        if not self.project_id:
            raise ValueError(
                "GOOGLE_CLOUD_PROJECT environment variable is required for Vertex AI. "
                "Set it to your GCP project ID."
            )
        
        # Initialize Vertex AI client with v1 API (per official docs)
        # Uses Application Default Credentials automatically
        self.client = genai.Client(
            http_options=HttpOptions(api_version="v1")
        )
        
        logger.info(
            f"Initialized Vertex AI Media Analysis: "
            f"model={default_model}, project={self.project_id}, location={self.location}"
        )
    
    async def analyze_media(
        self,
        file_url: str,
        question: str,
        model_name: Optional[str] = None,
        temperature: float = 0.1,
        audio_timestamp: bool = False,
        **kwargs
    ) -> MediaAnalysisResult:
        """
        Analyze media file using Gemini's multimodal capabilities via Vertex AI.
        
        Follows the official Vertex AI pattern from Google Cloud docs:
        https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/video-understanding
        https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/audio-understanding
        
        Args:
            file_url: GCS URI (gs://bucket/path) or HTTP/HTTPS URL (signed URLs)
            question: Question about the media
            model_name: Optional model override (default: gemini-2.0-flash-exp)
            temperature: Generation temperature (0.0-1.0, default: 0.1)
            audio_timestamp: Enable accurate timestamps for audio-only files (default: False)
                            For videos, timestamps are included automatically.
                            For audio-only, set to True for accurate timestamp generation.
            **kwargs: Additional parameters (max_tokens, etc.)
        
        Returns:
            MediaAnalysisResult with analysis
        
        Example:
            # Video analysis (timestamps automatic)
            result = await provider.analyze_media(
                file_url="gs://my-bucket/video.mp4",
                question="What is in the video?"
            )
            
            # Audio-only analysis (enable timestamps)
            result = await provider.analyze_media(
                file_url="gs://my-bucket/audio.mp3",
                question="Identify pauses and segment boundaries",
                audio_timestamp=True
            )
        """
        if not file_url or not question:
            raise ValueError("file_url and question are required")
        
        model = model_name or self.default_model
        
        try:
            normalized_url = self._normalize_file_url(file_url)

            logger.info(f"Analyzing media: {normalized_url[:80]}...")
            if normalized_url != file_url:
                logger.debug(
                    f"Normalized file URL for Vertex AI access: original={file_url[:80]}..., "
                    f"normalized={normalized_url[:80]}..."
                )
            logger.debug(f"Question: {question}")
            logger.debug(f"Model: {model}, Temperature: {temperature}")

            # Check if it's a YouTube URL (special handling)
            is_youtube = 'youtube.com/watch' in normalized_url or 'youtu.be/' in normalized_url

            if is_youtube:
                # YouTube URLs: Use FileData pattern with video/mp4 MIME type
                # Vertex AI requires mimeType even for YouTube URLs
                # See: https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/inference
                logger.info("Detected YouTube URL, using FileData pattern with video/mp4")
                from google.genai import types

                response = self.client.models.generate_content(
                    model=model,
                    contents=types.Content(
                        role="user",
                        parts=[
                            types.Part(
                                file_data=types.FileData(
                                    file_uri=normalized_url,
                                    mime_type="video/mp4"
                                )
                            ),
                            types.Part(text=question)
                        ]
                    )
                )
            elif normalized_url.startswith("gs://") or normalized_url.startswith("http://") or normalized_url.startswith("https://"):
                # GCS or HTTP URLs: Use Part.from_uri() with MIME type
                mime_type = self._get_mime_type(normalized_url)
                logger.debug(f"Using Part.from_uri() with mime_type={mime_type}")

                # Build generation_config for audio-only files
                # Per Vertex AI docs: audio-only files need audio_timestamp=True for accurate timestamps
                # Videos automatically include timestamps, so this is only for audio-only files
                from google.genai import types
                
                config_params = {}
                if self._is_audio_file(mime_type) or audio_timestamp:
                    config_params['audio_timestamp'] = True
                    logger.debug("Enabled audio_timestamp=True for accurate word-level timestamps")

                # Build request arguments
                generate_kwargs = {
                    "model": model,
                    "contents": [
                        Part.from_uri(
                            file_uri=normalized_url,
                            mime_type=mime_type
                        ),
                        Part.from_text(text=question)
                    ]
                }
                
                # Only add config if we have audio-specific settings
                if config_params:
                    generate_kwargs["config"] = types.GenerateContentConfig(**config_params)
                
                response = self.client.models.generate_content(**generate_kwargs)
            else:
                raise ValueError(
                    f"Unsupported file URL format: {file_url}. "
                    "Supported formats: YouTube URLs, GCS URIs (gs://), HTTP/HTTPS URLs. "
                    "For Vertex AI, files should be in Google Cloud Storage or YouTube."
                )
            
            analysis_text = response.text
            logger.info(f"Analysis completed: {len(analysis_text)} characters")
            
            # Extract usage metadata if available
            metadata = {}
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                metadata['prompt_tokens'] = getattr(usage, 'prompt_token_count', 0)
                metadata['response_tokens'] = getattr(usage, 'candidates_token_count', 0)
                metadata['total_tokens'] = getattr(usage, 'total_token_count', 0)
                logger.debug(f"Token usage: {metadata}")
            
            return MediaAnalysisResult(
                analysis=analysis_text,
                model_used=model,
                file_url=file_url,
                question=question,
                success=True,
                metadata=metadata
            )
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Media analysis failed: {error_msg}", exc_info=True)
            
            # User-friendly error messages
            if "authentication" in error_msg.lower() or "credentials" in error_msg.lower():
                user_error = (
                    "Authentication failed. Please ensure:\n"
                    "1. GOOGLE_APPLICATION_CREDENTIALS points to your service account JSON\n"
                    "2. GOOGLE_CLOUD_PROJECT is set to your GCP project ID\n"
                    "3. GOOGLE_GENAI_USE_VERTEXAI is set to 'True'"
                )
            elif "permission" in error_msg.lower() or "forbidden" in error_msg.lower():
                user_error = (
                    "Permission denied. Ensure your service account has:\n"
                    "- Vertex AI User role\n"
                    "- Storage Object Viewer role (for GCS files)"
                )
            elif "not found" in error_msg.lower():
                user_error = f"File not found: {file_url}. Please check the file path and permissions."
            elif "quota" in error_msg.lower() or "limit" in error_msg.lower():
                user_error = "API quota exceeded. Please try again later or increase your quota."
            elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                user_error = "Network connection error. Please check your internet connection."
            else:
                user_error = f"Media analysis failed: {error_msg}"
            
            return MediaAnalysisResult(
                analysis="",
                model_used=model,
                file_url=file_url,
                question=question,
                success=False,
                error_message=user_error
            )
    
    def _get_mime_type(self, file_url: str) -> str:
        """
        Determine MIME type from file extension.
        
        Args:
            file_url: File URL or path
        
        Returns:
            MIME type string
        """
        # Map extensions to MIME types
        mime_types = {
            # Videos
            'mp4': 'video/mp4',
            'mov': 'video/quicktime',
            'avi': 'video/x-msvideo',
            'flv': 'video/x-flv',
            'mpg': 'video/mpeg',
            'mpeg': 'video/mpeg',
            'webm': 'video/webm',
            'wmv': 'video/x-ms-wmv',
            '3gp': 'video/3gpp',
            
            # Images
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'bmp': 'image/bmp',
            'heic': 'image/heic',
            'heif': 'image/heif',
            
            # Audio
            'mp3': 'audio/mpeg',
            'wav': 'audio/wav',
            'aac': 'audio/aac',
            'ogg': 'audio/ogg',
            'flac': 'audio/flac',
            'aiff': 'audio/aiff',
            
            # Documents
            'pdf': 'application/pdf',
            'txt': 'text/plain',
            'html': 'text/html',
            'json': 'application/json',
        }
        
        # Extract path without query parameters
        url_path = file_url.split('?')[0]
        
        # Extract extension (handle URLs like /path/file.mp4)
        if '.' in url_path:
            ext = url_path.lower().rsplit('.', 1)[-1]
            mime_type = mime_types.get(ext)
            if mime_type:
                logger.debug(f"Detected MIME type from extension '{ext}': {mime_type}")
                return mime_type
        
        # Fallback: try to guess from common patterns
        logger.warning(f"Could not determine MIME type from extension in URL: {file_url}")
        logger.warning(f"Defaulting to video/mp4 for GCS URLs (most common case)")
        
        # Default to video/mp4 for GCS URLs (most common case in our app)
        # This is safer than application/octet-stream which Gemini rejects
        return 'video/mp4'
    
    def _is_audio_file(self, mime_type: str) -> bool:
        """
        Check if the MIME type represents an audio-only file.
        
        This is used to enable audio_timestamp configuration for audio-only files,
        as required by Vertex AI for accurate timestamp generation.
        Videos with audio tracks don't need this flag (timestamps are automatic).
        
        Args:
            mime_type: MIME type string (e.g., 'audio/mpeg', 'video/mp4')
        
        Returns:
            True if audio-only file, False otherwise
        """
        return mime_type.startswith('audio/')
    
    async def is_file_ready(self, file_url: str) -> bool:
        """
        Check if file is ready for analysis.
        
        For Vertex AI with GCS, files are always ready if they exist in the bucket.
        This method primarily exists for API compatibility.
        
        Args:
            file_url: GCS URI (gs://bucket/path) or HTTP URL
        
        Returns:
            True (GCS files are always ready once uploaded)
        """
        # For Vertex AI with GCS, files are immediately ready
        # No processing state like Gemini File API
        logger.debug(f"Checking file readiness: {file_url}")
        return True
    
    async def get_supported_file_types(self) -> list[str]:
        """
        Get list of supported file types for Gemini.
        
        Returns:
            List of supported MIME types
        """
        return [
            # Images
            "image/jpeg",
            "image/png",
            "image/webp",
            "image/gif",
            "image/heic",
            "image/heif",
            
            # Videos
            "video/mp4",
            "video/mpeg",
            "video/mov",
            "video/avi",
            "video/x-flv",
            "video/mpg",
            "video/webm",
            "video/wmv",
            "video/3gpp",
            
            # Audio
            "audio/wav",
            "audio/mp3",
            "audio/aiff",
            "audio/aac",
            "audio/ogg",
            "audio/flac",
            
            # Documents
            "application/pdf",
            "text/plain",
            "text/html",
            "text/css",
            "text/javascript",
            "application/json",
        ]

    def _normalize_file_url(self, file_url: str) -> str:
        """Normalize known GCS HTTPS URLs to gs:// URIs for Vertex AI access."""
        if not file_url:
            return file_url

        stripped = file_url.strip()

        # Already a gs:// URI
        if stripped.startswith("gs://"):
            return stripped

        try:
            parsed = urlparse(stripped)
        except Exception:
            logger.debug(f"Could not parse URL for normalization: {stripped}")
            return stripped

        host = parsed.netloc.lower()

        # Pattern: https://storage.googleapis.com/<bucket>/<object>
        if host == "storage.googleapis.com":
            path = parsed.path.lstrip('/')
            bucket, _, object_path = path.partition('/')
            if bucket and object_path:
                return f"gs://{bucket}/{object_path}"

        # Pattern: <bucket>.storage.googleapis.com/<object>
        if host.endswith(".storage.googleapis.com"):
            bucket = host[:-len(".storage.googleapis.com")]
            object_path = parsed.path.lstrip('/')
            if bucket and object_path:
                return f"gs://{bucket}/{object_path}"

        return stripped
