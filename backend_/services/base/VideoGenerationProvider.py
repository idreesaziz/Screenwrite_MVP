"""Abstract base class for video generation providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Any
from datetime import datetime
from PIL import Image


@dataclass
class VideoGenerationOperation:
    """Represents an async video generation operation."""
    operation_id: str
    prompt: str
    status: str  # 'processing', 'completed', 'failed'
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Optional[dict] = None
    # Provider-specific operation object (for internal use)
    _operation_obj: Optional[Any] = None


@dataclass
class GeneratedVideo:
    """Result of a completed video generation."""
    video_data: bytes
    prompt: str
    duration_seconds: float
    width: int
    height: int
    file_size: int
    format: str = "mp4"
    metadata: Optional[dict] = None


class VideoGenerationProvider(ABC):
    """
    Abstract interface for video generation providers.
    
    Video generation is typically an async operation:
    1. Call generate_video() → returns operation
    2. Poll check_generation_status() until complete
    3. Download video when done
    """
    
    @abstractmethod
    async def generate_video(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        aspect_ratio: str = "16:9",
        resolution: str = "720p",
        reference_image: Optional[Image.Image] = None,
        **kwargs
    ) -> VideoGenerationOperation:
        """
        Start async video generation.
        
        Args:
            prompt: Text description of video to generate
            negative_prompt: What to avoid in generation
            aspect_ratio: Video aspect ratio ("16:9", "9:16")
            resolution: Video resolution ("720p", "1080p")
            reference_image: Optional PIL Image for image-to-video generation
            **kwargs: Provider-specific options
            
        Returns:
            VideoGenerationOperation with operation_id for status checking
        """
        pass
    
    @abstractmethod
    async def check_generation_status(
        self,
        operation: VideoGenerationOperation,
        **kwargs
    ) -> VideoGenerationOperation:
        """
        Check status of an ongoing video generation operation.
        
        Args:
            operation: VideoGenerationOperation from generate_video()
            **kwargs: Provider-specific options
            
        Returns:
            Updated VideoGenerationOperation with current status
        """
        pass
    
    @abstractmethod
    async def download_generated_video(
        self,
        operation: VideoGenerationOperation,
        **kwargs
    ) -> GeneratedVideo:
        """
        Download completed video.
        
        Args:
            operation: Completed VideoGenerationOperation
            **kwargs: Provider-specific options
            
        Returns:
            GeneratedVideo with video bytes and metadata
            
        Raises:
            ValueError: If operation is not completed
        """
        pass
    
    @abstractmethod
    async def cancel_generation(
        self,
        operation: VideoGenerationOperation,
        **kwargs
    ) -> bool:
        """
        Cancel an ongoing video generation operation.
        
        Args:
            operation: VideoGenerationOperation to cancel
            **kwargs: Provider-specific options
            
        Returns:
            True if cancelled successfully
        """
        pass
