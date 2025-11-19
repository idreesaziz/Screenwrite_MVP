"""
FastAPI Dependency Injection Setup.

Provides factory functions for creating provider instances with proper
configuration and dependency injection for FastAPI endpoints.
"""

import os
from functools import lru_cache
from typing import Optional

from services.base.MediaAnalysisProvider import MediaAnalysisProvider
from services.base.StorageProvider import StorageProvider
from services.base.ChatProvider import ChatProvider
from services.base.MediaProvider import MediaProvider
from services.base.ImageGenerationProvider import ImageGenerationProvider
from services.base.VideoGenerationProvider import VideoGenerationProvider
from services.base.VoiceGenerationProvider import VoiceGenerationProvider
from services.google.GeminiMediaAnalysisProvider import GeminiMediaAnalysisProvider
from services.google.GCStorageProvider import GCStorageProvider
from services.google.GeminiChatProvider import GeminiChatProvider
from services.anthropic.ClaudeChatProvider import ClaudeChatProvider
from services.openai.OpenAIChatProvider import OpenAIChatProvider
from services.pexels.PexelsMediaProvider import PexelsMediaProvider
from services.google.ImagenGenerationProvider import ImagenGenerationProvider
from services.google.VEOGenerationProvider import VEOGenerationProvider
from services.google.GoogleTTSProvider import GoogleTTSProvider


@lru_cache()
def get_media_analysis_provider() -> MediaAnalysisProvider:
    """
    Factory function for MediaAnalysisProvider.
    
    Returns a singleton instance of the configured media analysis provider.
    Uses @lru_cache() to ensure only one instance is created.
    
    Currently returns GeminiMediaAnalysisProvider (Vertex AI).
    Future: Support multiple providers via env variable.
    
    Returns:
        MediaAnalysisProvider instance (GeminiMediaAnalysisProvider)
    """
    provider_type = os.getenv("MEDIA_ANALYSIS_PROVIDER", "gemini")
    
    if provider_type == "gemini":
        return GeminiMediaAnalysisProvider(
            project_id=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
            default_model=os.getenv("MEDIA_ANALYSIS_MODEL", "gemini-2.5-flash")
        )
    else:
        raise ValueError(f"Unsupported media analysis provider: {provider_type}")


@lru_cache()
def get_storage_provider() -> StorageProvider:
    """
    Factory function for StorageProvider.
    
    Returns a singleton instance of the configured storage provider.
    Uses @lru_cache() to ensure only one instance is created.
    
    Currently returns GCStorageProvider (Google Cloud Storage).
    
    Returns:
        StorageProvider instance (GCStorageProvider)
    """
    return GCStorageProvider(
        bucket_name=os.getenv("GCS_BUCKET_NAME", "screenwrite-media"),
        project_id=os.getenv("GOOGLE_CLOUD_PROJECT")
    )


@lru_cache()
def get_chat_provider() -> ChatProvider:
    """
    Factory function for ChatProvider (default/agent provider).
    
    Returns a singleton instance of the configured chat provider.
    Uses @lru_cache() to ensure only one instance is created.
    
    Currently returns GeminiChatProvider (Google AI API).
    Future: Support multiple providers via env variable.
    
    Returns:
        ChatProvider instance (GeminiChatProvider)
    """
    provider_type = os.getenv("CHAT_PROVIDER", "gemini")
    
    if provider_type == "gemini":
        return GeminiChatProvider(
            project_id=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
            default_model_name=os.getenv("CHAT_MODEL", "gemini-2.5-flash"),
            default_temperature=1.0,
            default_thinking_budget=8000
        )
    elif provider_type == "claude":
        return ClaudeChatProvider(
            default_model_name=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5"),
            default_temperature=1.0,
            default_thinking_budget=2000
        )
    elif provider_type == "openai":
        return OpenAIChatProvider(
            default_model_name=os.getenv("OPENAI_MODEL", "gpt-4.1"),
            default_temperature=1.0,
            default_reasoning_effort="medium"
        )
    else:
        raise ValueError(f"Unsupported chat provider: {provider_type}")


def get_chat_provider_by_name(provider_name: str, thinking_budget: int = 8000) -> ChatProvider:
    """
    Factory function for creating ChatProvider instances dynamically.
    
    This allows per-request provider selection (e.g., from frontend UI).
    NOT cached - creates new instance each time for per-request flexibility.
    
    Args:
        provider_name: Provider name ("gemini" or "claude")
        thinking_budget: Thinking budget for extended thinking mode
    
    Returns:
        ChatProvider instance (GeminiChatProvider or ClaudeChatProvider)
    
    Raises:
        ValueError: If provider_name is not supported
    """
    provider_name = provider_name.lower()
    
    if provider_name == "gemini":
        return GeminiChatProvider(
            project_id=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
            default_model_name=os.getenv("CHAT_MODEL", "gemini-2.5-flash"),
            default_temperature=1.0,
            default_thinking_budget=thinking_budget
        )
    elif provider_name == "claude":
        return ClaudeChatProvider(
            default_model_name=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5"),
            default_temperature=1.0,
            default_thinking_budget=2000
        )
    elif provider_name == "openai":
        return OpenAIChatProvider(
            default_model_name=os.getenv("OPENAI_MODEL", "gpt-4.1"),
            default_temperature=1.0,
            default_reasoning_effort="medium"
        )
    else:
        raise ValueError(f"Unsupported chat provider: {provider_name}")


def get_media_analysis_service():
    """
    Factory function for MediaAnalysisService.
    
    Creates a new MediaAnalysisService instance with injected dependencies.
    Note: Does not use @lru_cache() since the service is stateless and
    dependencies are already cached.
    
    Returns:
        MediaAnalysisService instance
    """
    from business_logic.analyze_media import MediaAnalysisService
    
    return MediaAnalysisService(
        media_analysis_provider=get_media_analysis_provider(),
        storage_provider=get_storage_provider()
    )


def get_composition_service():
    """
    Factory function for CompositionGenerationService.
    
    Creates a new CompositionGenerationService instance with injected
    chat provider dependency.
    
    Returns:
        CompositionGenerationService instance
    """
    from business_logic.generate_composition import CompositionGenerationService
    
    return CompositionGenerationService(
        chat_provider=get_chat_provider()
    )


@lru_cache()
def get_media_provider() -> MediaProvider:
    """
    Factory function for MediaProvider.
    
    Returns a singleton instance of the configured media provider.
    Uses @lru_cache() to ensure only one instance is created.
    
    Currently returns PexelsMediaProvider.
    Future: Support Shutterstock, Getty, etc. via env variable.
    
    Returns:
        MediaProvider instance (PexelsMediaProvider)
    """
    provider_type = os.getenv("MEDIA_PROVIDER", "pexels")
    
    if provider_type == "pexels":
        return PexelsMediaProvider(
            api_key=os.getenv("PEXELS_API_KEY"),
            gcs_bucket=os.getenv("GCS_BUCKET_NAME", "screenwrite-media"),
            gemini_provider=get_chat_provider()
        )
    else:
        raise ValueError(f"Unsupported media provider: {provider_type}")


def get_stock_media_service():
    """
    Factory function for StockMediaService.
    
    Creates a new StockMediaService instance with injected dependencies.
    
    Returns:
        StockMediaService instance
    """
    from business_logic.fetch_media import StockMediaService
    
    return StockMediaService(
        media_provider=get_media_provider(),
        storage_provider=get_storage_provider()
    )


@lru_cache()
def get_image_generation_provider() -> ImageGenerationProvider:
    """
    Factory function for ImageGenerationProvider.
    
    Returns a singleton instance of the configured image generation provider.
    Uses @lru_cache() to ensure only one instance is created.
    
    Currently returns ImagenGenerationProvider (Google Imagen).
    
    Returns:
        ImageGenerationProvider instance (ImagenGenerationProvider)
    """
    return ImagenGenerationProvider(
        project_id=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
        default_model_name=os.getenv("IMAGEN_MODEL", "imagen-3.0-generate-001")
    )


@lru_cache()
def get_video_generation_provider() -> VideoGenerationProvider:
    """
    Factory function for VideoGenerationProvider.
    
    Returns a singleton instance of the configured video generation provider.
    Uses @lru_cache() to ensure only one instance is created.
    
    Currently returns VEOGenerationProvider (Google Veo).
    
    Returns:
        VideoGenerationProvider instance (VEOGenerationProvider)
    """
    return VEOGenerationProvider(
        project_id=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
        model_name=os.getenv("VEO_MODEL", "veo-3.0-fast-generate-001"),
        gcs_bucket=os.getenv("GCS_BUCKET_NAME", "screenwrite-media")
    )


@lru_cache()
def get_voice_generation_provider() -> VoiceGenerationProvider:
    """
    Factory function for VoiceGenerationProvider.
    
    Returns a singleton instance of the configured voice generation provider.
    Uses @lru_cache() to ensure only one instance is created.
    
    Currently returns GoogleTTSProvider (Google Cloud Text-to-Speech).
    
    Returns:
        VoiceGenerationProvider instance (GoogleTTSProvider)
    """
    return GoogleTTSProvider()


@lru_cache()
def get_media_generation_service():
    """
    Factory function for MediaGenerationService.
    
    Returns a singleton instance to maintain active_operations state.
    Uses @lru_cache() to ensure only one instance is created.
    
    Returns:
        MediaGenerationService instance
    """
    from business_logic.generate_media import MediaGenerationService
    
    return MediaGenerationService(
        image_provider=get_image_generation_provider(),
        video_provider=get_video_generation_provider(),
        voice_provider=get_voice_generation_provider(),
        storage_provider=get_storage_provider()
    )


def get_agent_service():
    """
    Factory function for AgentService.
    
    Creates a new AgentService instance with injected chat provider dependency.
    
    Returns:
        AgentService instance
    """
    from business_logic.invoke_agent import AgentService
    
    return AgentService(
        chat_provider=get_chat_provider()
    )
