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
from services.google.GeminiMediaAnalysisProvider import GeminiMediaAnalysisProvider
from services.google.GCStorageProvider import GCStorageProvider


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
            default_model=os.getenv("MEDIA_ANALYSIS_MODEL", "gemini-2.0-flash-exp")
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
