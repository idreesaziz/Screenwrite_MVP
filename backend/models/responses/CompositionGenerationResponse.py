from typing import Dict, Optional
from pydantic import BaseModel, Field


class CompositionGenerationResponse(BaseModel):
    """Response from composition generation"""
    
    success: bool = Field(
        description="Whether composition generation was successful"
    )
    
    composition_code: str = Field(
        description="Generated composition blueprint as JSON string (array of tracks)"
    )
    
    explanation: str = Field(
        description="Human-readable explanation of what was generated"
    )
    
    duration: float = Field(
        description="Total duration of the composition in seconds"
    )
    
    model_used: str = Field(
        description="AI model that was used for generation"
    )
    
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if generation failed"
    )
    
    metadata: Optional[Dict] = Field(
        default=None,
        description="Additional metadata (token usage, thinking time, etc.)"
    )
