"""
Agent Service - Business Logic Layer.

Orchestrates conversational AI agent interactions for video editing assistance.
"""

import logging
import json
from typing import Optional, List, Dict, Any

from services.base.ChatProvider import ChatProvider
from prompts.agent_prompts import build_agent_system_prompt

logger = logging.getLogger(__name__)


class AgentService:
    """
    Service for AI-powered conversational video editing agent.
    
    Handles:
    - Conversational understanding of user editing requests
    - Context-aware responses based on composition state
    - Structured output parsing for different action types
    - Integration with chat provider for AI responses
    """
    
    def __init__(
        self,
        chat_provider: ChatProvider
    ):
        """
        Initialize the agent service.
        
        Args:
            chat_provider: Provider for AI chat completions
        """
        self.chat_provider = chat_provider
        logger.info(f"AgentService initialized with provider: {type(chat_provider).__name__}")
    
    async def chat(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        composition_json: Optional[str] = None,
        media_library: Optional[List[str]] = None,
        duration: Optional[float] = None,
        user_id: str = None,
        session_id: str = None,
        model_name: Optional[str] = None,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Process user message and generate agent response.
        
        Args:
            user_message: The user's message
            conversation_history: Recent conversation for context
            composition_json: Current composition state as JSON string
            media_library: List of available media filenames
            duration: Total composition duration
            user_id: User ID for logging
            session_id: Session ID for logging
            model_name: Optional model override
            temperature: Generation temperature
        
        Returns:
            Dictionary with type, content, and optional action fields
        """
        logger.info(f"Agent chat request from user={user_id}, session={session_id}")
        logger.debug(f"User message: {user_message[:100]}...")
        
        try:
            # Build system prompt
            system_prompt = build_agent_system_prompt()
            
            # Build context for the agent
            context_parts = []
            
            # Add composition context
            if composition_json:
                context_parts.append(f"**Current Composition Blueprint:**\n```json\n{composition_json}\n```")
            else:
                context_parts.append("**Current Composition:** No composition loaded (empty timeline)")
            
            # Add media library context
            if media_library:
                media_list = "\n".join([f"- {filename}" for filename in media_library])
                context_parts.append(f"**Available Media Files:**\n{media_list}")
            else:
                context_parts.append("**Available Media Files:** No media files in library")
            
            # Add duration context
            if duration is not None:
                context_parts.append(f"**Composition Duration:** {duration} seconds")
            
            # Add conversation history context - INCLUDE ALL MESSAGES WITH FULL CONTENT
            # This is critical for the workflow loop to see analysis results and previous exchanges
            if conversation_history:
                logger.info(f"📚 Including {len(conversation_history)} messages in conversation history")
                history_text = "\n".join([
                    f"- {msg.get('role', 'unknown')}: {msg.get('content', '')}"
                    for msg in conversation_history  # ALL messages, no truncation
                ])
                context_parts.append(f"**Complete Conversation History:**\n{history_text}")
                logger.debug(f"History preview (first 500 chars): {history_text[:500]}...")
            
            # Combine all context
            full_context = "\n\n".join(context_parts)
            
            # Build user prompt with context
            user_prompt = f"""{full_context}

**User Request:**
{user_message}

Respond with structured JSON containing "type" and "content" fields, plus any additional fields needed for the action type."""
            
            # Call chat provider with structured output schema
            logger.debug("Calling chat provider for agent response...")
            from services.base.ChatProvider import ChatMessage
            
            messages = [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_prompt)
            ]
            
            # Define strict response schema for Gemini
            response_schema = {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["chat", "sleep", "edit", "probe", "generate", "fetch"],
                        "description": "The action type for this response"
                    },
                    "content": {
                        "type": "string",
                        "description": "The main message content to display to the user"
                    },
                    "fileName": {
                        "type": "string",
                        "description": "For probe type: filename to analyze OR YouTube URL",
                        "nullable": True
                    },
                    "question": {
                        "type": "string",
                        "description": "For probe type: question to ask about the media",
                        "nullable": True
                    },
                    "content_type": {
                        "type": "string",
                        "enum": ["image", "video"],
                        "description": "For generate type: type of media to generate",
                        "nullable": True
                    },
                    "prompt": {
                        "type": "string",
                        "description": "For generate type: detailed generation prompt",
                        "nullable": True
                    },
                    "suggestedName": {
                        "type": "string",
                        "description": "For generate type: suggested filename without extension",
                        "nullable": True
                    },
                    "seedImageFileName": {
                        "type": "string",
                        "description": "For video generation: optional seed image filename from media library",
                        "nullable": True
                    },
                    "query": {
                        "type": "string",
                        "description": "For fetch type: search query for stock media",
                        "nullable": True
                    }
                },
                "required": ["type", "content"]
            }
            
            agent_response = await self.chat_provider.generate_chat_response_with_schema(
                messages=messages,
                response_schema=response_schema,
                model_name=model_name,
                temperature=temperature
            )
            
            logger.info(f"Agent response type: {agent_response.get('type')}")
            
            # Validate response type
            valid_types = ["chat", "sleep", "edit", "probe", "generate", "fetch"]
            if agent_response.get("type") not in valid_types:
                logger.warning(f"Invalid response type: {agent_response.get('type')}, defaulting to 'sleep'")
                agent_response["type"] = "sleep"
            
            # Add metadata placeholder (token usage would come from model if available)
            if "metadata" not in agent_response:
                agent_response["metadata"] = {
                    "model_used": model_name or "gemini-2.0-flash-exp"
                }
            
            return agent_response
        
        except Exception as e:
            logger.error(f"Unexpected error in agent chat: {str(e)}", exc_info=True)
            return {
                "type": "sleep",
                "content": "Something went wrong with the server. Would you like to retry or try something else?",
                "error": str(e)
            }
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """
        Get agent capabilities and available action types.
        
        Returns:
            Dictionary describing agent capabilities
        """
        return {
            "action_types": {
                "chat": "Informational messages, workflow continues automatically",
                "sleep": "Messages requiring user input, workflow stops and waits",
                "edit": "Direct editing instructions for composition changes",
                "probe": "Media content analysis requests",
                "generate": "Media generation requests (images: 16:9 1920x1080, videos: 8s 16:9 1920x1080)",
                "fetch": "Stock video search and selection requests"
            },
            "features": [
                "Conversational video editing assistance",
                "Context-aware composition understanding",
                "Media library awareness",
                "Stock footage integration",
                "AI-powered media generation",
                "Content analysis and probing",
                "Step-by-step editing workflows"
            ],
            "workflow_steps": [
                "1. User requests edit",
                "2. Agent creates detailed plan (type: sleep)",
                "3. User confirms plan",
                "4. Agent executes with instructions (type: edit)",
                "5. Implementation processes edit",
                "6. Repeat as needed"
            ]
        }
