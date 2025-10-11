"""
Abstract base class for AI-powered media analysis providers.

This provider handles multimodal AI analysis of various media types:
- Images (JPEG, PNG, WebP, etc.)
- Videos (MP4, MOV, YouTube URLs, etc.)
- Audio files (MP3, WAV, etc.)
- Documents (PDF, etc.)

Supports asking questions about media content and getting AI-generated answers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class MediaAnalysisResult:
    """Result of media analysis operation"""
    analysis: str  # AI-generated analysis/answer
    model_used: str  # Model that performed the analysis
    file_url: str  # URL/URI of analyzed file
    question: str  # Question that was asked
    success: bool
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None  # Additional info (tokens used, processing time, etc.)
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class MediaAnalysisProvider(ABC):
    """
    Abstract provider for AI-powered media analysis.
    
    Implementations should support:
    - Multiple file sources (URLs, GCS URIs, uploaded files, etc.)
    - Various media types (images, videos, audio, documents)
    - Dynamic model selection
    - File state validation (checking if file is ready for analysis)
    """
    
    @abstractmethod
    async def analyze_media(
        self,
        file_url: str,
        question: str,
        model_name: Optional[str] = None,
        temperature: float = 0.1,
        **kwargs
    ) -> MediaAnalysisResult:
        """
        Analyze media file and answer a question about it.
        
        Args:
            file_url: URL/URI of the media file. Can be:
                     - YouTube URL (https://youtube.com/watch?v=...)
                     - GCS URI (gs://bucket/path/to/file)
                     - Gemini File ID (files/abc123...)
                     - Signed URL (https://storage.googleapis.com/...)
            question: Question to ask about the media
            model_name: Optional model name (provider-specific)
            temperature: Temperature for generation (0.0-1.0)
            **kwargs: Additional provider-specific parameters
        
        Returns:
            MediaAnalysisResult with analysis text and metadata
        
        Raises:
            ValueError: If file_url or question is invalid
            Exception: If analysis fails
        """
        pass
    
    @abstractmethod
    async def is_file_ready(
        self,
        file_url: str
    ) -> bool:
        """
        Check if file is ready for analysis.
        
        Some providers require files to be processed before analysis
        (e.g., Gemini Files API has PROCESSING → ACTIVE states).
        
        Args:
            file_url: URL/URI of the media file
        
        Returns:
            True if file is ready for analysis, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_supported_file_types(self) -> list[str]:
        """
        Get list of supported file types/extensions.
        
        Returns:
            List of supported MIME types or file extensions
            Example: ["image/jpeg", "video/mp4", "audio/mp3", "application/pdf"]
        """
        pass
