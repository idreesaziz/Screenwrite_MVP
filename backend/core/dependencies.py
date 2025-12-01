"""
FastAPI Dependency Injection Setup.

Provides factory functions for creating provider instances with proper
configuration and dependency injection for FastAPI endpoints.
"""

import logging
import os
from functools import lru_cache
from typing import Optional, Tuple

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
from services.google.Gemini3ChatProvider import Gemini3ChatProvider
from services.anthropic.ClaudeChatProvider import ClaudeChatProvider
from services.openai.OpenAIChatProvider import OpenAIChatProvider
from services.pexels.PexelsMediaProvider import PexelsMediaProvider
from services.google.ImagenGenerationProvider import ImagenGenerationProvider
from services.google.VEOGenerationProvider import VEOGenerationProvider
from services.google.GoogleTTSProvider import GoogleTTSProvider


logger = logging.getLogger(__name__)


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


def _build_chat_provider(provider_key: Optional[str], thinking_budget: int = 8000) -> ChatProvider:
    """Instantiate a chat provider based on the normalized provider key."""
    key = (provider_key or "gemini").strip().lower()
    
    if key == "gemini":
        return GeminiChatProvider(
            project_id=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
            default_model_name=os.getenv("CHAT_MODEL", "gemini-2.5-flash"),
            default_temperature=1.0,
            default_thinking_budget=thinking_budget
        )
    elif key in {"gemini-3", "gemini-3-low", "gemini-3-high"}:
        level = "high" if key.endswith("high") else "low"
        return Gemini3ChatProvider(
            project_id=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location="global",
            default_model_name="gemini-3-pro-preview",
            default_temperature=1.0,
            default_thinking_level=level
        )
    elif key == "claude":
        return ClaudeChatProvider(
            default_model_name=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5"),
            default_temperature=1.0,
            default_thinking_budget=2000
        )
    elif key == "openai":
        return OpenAIChatProvider(
            default_model_name=os.getenv("OPENAI_MODEL", "gpt-4.1"),
            default_temperature=1.0,
            default_reasoning_effort="medium"
        )
    else:
        raise ValueError(f"Unsupported chat provider: {provider_key}")


def _normalize_gemini3_provider_key(provider_key: str) -> str:
    """Collapse gemini-3 aliases down to explicit low/high variants."""
    key = provider_key.lower()
    if key == "gemini-3":
        return "gemini-3-low"
    return key


def resolve_chat_provider(
    provider_name: Optional[str],
    requested_model: Optional[str],
    thinking_budget: int = 8000
) -> Tuple[ChatProvider, Optional[str]]:
    """Return a provider instance and a sanitized model override.
    
    Ensures Gemini 2.5 requests use the Gemini provider, Gemini 3 requests
    use the Gemini 3 provider, and prevents unsupported combinations where
    thinking levels would be sent to non-Gemini-3 models.
    """
    normalized_provider = (provider_name or "gemini").strip().lower()
    model_override = requested_model
    model_lower = model_override.lower() if model_override else None
    disallowed_overrides = {"gemini", "claude", "openai", "gemini-3-low", "gemini-3-high"}
    if model_lower in disallowed_overrides:
        logger.debug("Ignoring reserved model override '%s'", model_override)
        model_override = None
        model_lower = None
    is_gemini3_model = bool(model_lower and model_lower.startswith("gemini-3"))
    provider_key = normalized_provider
    if is_gemini3_model and provider_key == "gemini":
        provider_key = "gemini-3-low"
        logger.info("Routing Gemini 3 model '%s' through Gemini 3 provider", model_override)
    if provider_key in {"gemini-3", "gemini-3-low", "gemini-3-high"}:
        provider_key = _normalize_gemini3_provider_key(provider_key)
        if model_override and not is_gemini3_model:
            logger.warning(
                "Dropping non-Gemini-3 override '%s' for provider '%s'",
                model_override,
                provider_key
            )
            model_override = None
    provider = _build_chat_provider(provider_key, thinking_budget)
    return provider, model_override


@lru_cache()
def get_chat_provider() -> ChatProvider:
    """Singleton ChatProvider for default use cases."""
    return _build_chat_provider(os.getenv("CHAT_PROVIDER", "gemini"))


def get_chat_provider_by_name(provider_name: str, thinking_budget: int = 8000) -> ChatProvider:
    """Backwards-compatible factory for explicitly requested providers."""
    return _build_chat_provider(provider_name, thinking_budget)


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
