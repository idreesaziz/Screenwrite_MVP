"""Services base package - Abstract provider interfaces."""

from services.base.ChatProvider import ChatProvider, ChatMessage, ChatResponse
from services.base.ImageGenerationProvider import (
    ImageGenerationProvider,
    ImageGenerationRequest,
    ImageGenerationResponse,
    GeneratedImage,
    ImageUpscaleRequest
)

__all__ = [
    'ChatProvider',
    'ChatMessage',
    'ChatResponse',
    'ImageGenerationProvider',
    'ImageGenerationRequest',
    'ImageGenerationResponse',
    'GeneratedImage',
    'ImageUpscaleRequest'
]
