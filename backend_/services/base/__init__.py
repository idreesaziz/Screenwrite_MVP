"""Services base package - Abstract provider interfaces."""

from services.base.ChatProvider import ChatProvider, ChatMessage, ChatResponse
from services.base.ImageGenerationProvider import (
    ImageGenerationProvider,
    ImageGenerationRequest,
    ImageGenerationResponse,
    GeneratedImage,
    ImageUpscaleRequest
)
from services.base.MediaProvider import (
    MediaProvider,
    MediaSearchRequest,
    MediaSearchResponse,
    MediaDownloadRequest,
    MediaItem,
    CuratedMediaItem,
    VideoFile,
    MediaCreator,
    MediaType,
    VideoOrientation
)

__all__ = [
    'ChatProvider',
    'ChatMessage',
    'ChatResponse',
    'ImageGenerationProvider',
    'ImageGenerationRequest',
    'ImageGenerationResponse',
    'GeneratedImage',
    'ImageUpscaleRequest',
    'MediaProvider',
    'MediaSearchRequest',
    'MediaSearchResponse',
    'MediaDownloadRequest',
    'MediaItem',
    'CuratedMediaItem',
    'VideoFile',
    'MediaCreator',
    'MediaType',
    'VideoOrientation'
]
