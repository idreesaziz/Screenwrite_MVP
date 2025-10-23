from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class CompositionGenerationRequest(BaseModel):
    """Request to generate or modify a video composition"""
    
    user_request: str = Field(
        description="User's description of what they want to create or modify"
    )
    
    preview_settings: Dict[str, Any] = Field(
        description="Current preview settings (width, height, fps, etc.)",
        examples=[{"width": 1920, "height": 1080, "fps": 30}]
    )
    
    media_library: Optional[List[Dict[str, Any]]] = Field(
        default=[],
        description="Available media files in user's library"
    )
    
    current_composition: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Current composition blueprint (array of tracks) for incremental editing"
    )
    
    preview_frame: Optional[str] = Field(
        default=None,
        description="Base64 encoded screenshot of current preview frame"
    )
    
    model_name: Optional[str] = Field(
        default=None,
        description="Override the default AI model (e.g., 'gemini-2.5-flash', 'gemini-2.0-flash-thinking-exp')"
    )
    
    provider: Optional[str] = Field(
        default="gemini",
        description="AI provider to use for generation ('gemini' or 'claude')"
    )
    
    temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="Temperature for generation (0.0-2.0, lower = more deterministic)"
    )
