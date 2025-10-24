"""
Agent Request Models.

Pydantic models for conversational agent API requests.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class AgentMessage(BaseModel):
    """Individual message in the conversation."""
    
    id: str = Field(
        ...,
        description="Unique message ID (UUID)"
    )
    
    content: str = Field(
        ...,
        description="Message content text",
        min_length=1
    )
    
    isUser: bool = Field(
        ...,
        description="True if message is from user, False if from assistant"
    )
    
    timestamp: str = Field(
        ...,
        description="ISO 8601 timestamp of when message was created"
    )


class AgentRequest(BaseModel):
    """Request model for agent chat endpoint."""
    
    messages: List[AgentMessage] = Field(
        ...,
        description="Conversation history (chronological order)",
        min_length=1
    )
    
    currentComposition: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Current timeline blueprint (array of tracks with clips)"
    )
    
    mediaLibrary: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list,
        description="Available media files in user's library"
    )
    
    compositionDuration: Optional[float] = Field(
        None,
        description="Current composition duration in seconds",
        ge=0
    )
    
    provider: Optional[str] = Field(
        default="gemini",
        description="AI provider to use for agent chat ('gemini', 'claude', or 'openai')"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {
                        "id": "msg-1",
                        "content": "What's on my timeline?",
                        "isUser": True,
                        "timestamp": "2025-10-11T10:30:00Z"
                    }
                ],
                "currentComposition": [
                    {
                        "clips": [
                            {
                                "id": "clip-1",
                                "startTimeInSeconds": 0,
                                "endTimeInSeconds": 5,
                                "element": {
                                    "elements": [
                                        "AbsoluteFill;id:root;parent:null",
                                        "h1;id:title;parent:root;text:Hello"
                                    ]
                                }
                            }
                        ]
                    }
                ],
                "mediaLibrary": [
                    {
                        "name": "background.mp4",
                        "type": "video",
                        "duration": 10.5,
                        "url": "gs://bucket/background.mp4"
                    }
                ],
                "compositionDuration": 5.0
            }
        }
