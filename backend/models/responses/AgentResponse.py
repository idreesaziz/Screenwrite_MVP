"""
Agent Chat Response Models.

Pydantic models for conversational agent API responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class AgentResponse(BaseModel):
    """Response model for agent chat endpoint."""
    
    type: str = Field(
        ...,
        description="Response type: 'info', 'chat', 'edit', 'probe', 'generate', 'fetch'",
        examples=["info", "chat", "edit", "probe", "generate", "fetch"]
    )
    
    content: str = Field(
        ...,
        description="The agent's message content"
    )
    
    # Optional fields for specific action types
    fileName: Optional[str] = Field(
        None,
        description="For probe type: filename to analyze OR YouTube URL"
    )
    
    question: Optional[str] = Field(
        None,
        description="For probe type: question to ask about the media"
    )
    
    content_type: Optional[str] = Field(
        None,
        description="For generate type: 'image' or 'video'"
    )
    
    prompt: Optional[str] = Field(
        None,
        description="For generate type: generation prompt"
    )
    
    suggestedName: Optional[str] = Field(
        None,
        description="For generate type: suggested filename without extension"
    )
    
    seedImageFileName: Optional[str] = Field(
        None,
        description="For video generation: optional seed image filename from media library"
    )
    
    query: Optional[str] = Field(
        None,
        description="For fetch type: search query for stock media"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata (token usage, model info, etc.)"
    )
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "type": "chat",
                    "content": "I'll add a welcome title at the beginning. The text will fade in at 0 seconds and stay visible until 3 seconds. Does this sound good? Say 'yes' to proceed.",
                    "metadata": {
                        "total_tokens": 1250
                    }
                },
                {
                    "type": "edit",
                    "content": "Add a text clip with 'Welcome' starting at 0 seconds, ending at 3 seconds. Apply a fade-in transition from 0 to 0.5 seconds. Style the text with large bold font, white color, and center alignment.",
                    "metadata": {
                        "total_tokens": 1480
                    }
                },
                {
                    "type": "probe",
                    "content": "Let me analyze the background video to see what colors would work best for the text overlay.",
                    "fileName": "background.mp4",
                    "question": "What are the dominant colors and overall mood of this video? Where is the main visual focus located?",
                    "metadata": {
                        "total_tokens": 950
                    }
                },
                {
                    "type": "generate",
                    "content_type": "image",
                    "content": "I'll create a professional sunset background image for you.",
                    "prompt": "A dramatic golden hour sunset over mountain peaks with warm orange and purple sky tones, cinematic lighting, high detail, professional photography style, composed for 16:9 widescreen format",
                    "suggestedName": "sunset_mountain_landscape",
                    "metadata": {
                        "total_tokens": 1100
                    }
                },
                {
                    "type": "generate",
                    "content_type": "video",
                    "content": "I'll generate ocean waves footage for the background.",
                    "prompt": "Gentle ocean waves rolling onto a sandy beach at sunset, slow motion, warm golden lighting, cinematic shot, 8 seconds of peaceful repetitive motion",
                    "suggestedName": "ocean_waves_sunset",
                    "seedImageFileName": None,
                    "metadata": {
                        "total_tokens": 1200
                    }
                },
                {
                    "type": "fetch",
                    "content": "I'll search for stock footage of city traffic for you.",
                    "query": "busy city traffic at night with car lights",
                    "metadata": {
                        "total_tokens": 890
                    }
                }
            ]
        }
