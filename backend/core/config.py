"""
Core configuration management using Pydantic BaseSettings.

All environment variables are loaded and validated here.
"""

import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class GoogleCloudConfig(BaseSettings):
    """Google Cloud Platform configuration"""
    project_id: str = Field(default="gen-lang-client-0896424835", alias="GOOGLE_CLOUD_PROJECT")
    location: str = Field(default="us-central1", alias="GOOGLE_CLOUD_LOCATION")
    credentials_path: Optional[str] = Field(default=None, alias="GOOGLE_APPLICATION_CREDENTIALS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env


class GeminiConfig(BaseSettings):
    """Gemini AI configuration"""
    api_key: str = Field(..., alias="GEMINI_API_KEY")
    default_chat_model: str = Field(default="gemini-2.0-flash-exp")
    default_analysis_model: str = Field(default="gemini-2.0-flash-exp")
    default_temperature: float = Field(default=0.7)
    default_thinking_budget: int = Field(default=-1)  # -1 = unlimited
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env


class ImagenConfig(BaseSettings):
    """Imagen configuration"""
    default_model: str = Field(default="imagen-4.0-fast-generate-001")
    default_aspect_ratio: str = Field(default="1:1")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


class VeoConfig(BaseSettings):
    """Veo video generation configuration"""
    default_model: str = Field(default="veo-3.0-fast-generate-001")
    default_resolution: str = Field(default="720p")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


class PexelsConfig(BaseSettings):
    """Pexels stock media configuration"""
    api_key: str = Field(..., alias="PEXELS_API_KEY")
    default_per_page: int = Field(default=50)
    max_curated_results: int = Field(default=3)
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


class GCSConfig(BaseSettings):
    """Google Cloud Storage configuration"""
    bucket_name: str = Field(default="screenwrite-media", alias="GCS_BUCKET_NAME")
    signed_url_expiration_days: int = Field(default=7)
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


class AuthConfig(BaseSettings):
    """Authentication configuration"""
    supabase_url: str = Field(default="https://placeholder.supabase.co", alias="SUPABASE_URL")
    supabase_jwt_secret: str = Field(..., alias="SUPABASE_JWT_SECRET")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


class AppConfig(BaseSettings):
    """Main application configuration"""
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")
    api_version: str = Field(default="v1")
    cors_origins: list[str] = Field(default=["*"])
    
    # Sub-configurations (all use default_factory for proper BaseSettings nesting)
    google_cloud: GoogleCloudConfig = Field(default_factory=GoogleCloudConfig)
    gemini: GeminiConfig = Field(default_factory=GeminiConfig)
    imagen: ImagenConfig = Field(default_factory=ImagenConfig)
    veo: VeoConfig = Field(default_factory=VeoConfig)
    pexels: PexelsConfig = Field(default_factory=PexelsConfig)
    gcs: GCSConfig = Field(default_factory=GCSConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_config() -> AppConfig:
    """
    Get application configuration (cached singleton).
    
    Returns:
        AppConfig instance loaded from environment variables
    """
    return AppConfig()
