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
        conversation_history: List[Dict[str, str]],
        composition_json: Optional[str] = None,
        media_library: Optional[List[Dict[str, str]]] = None,
        duration: Optional[float] = None,
        user_id: str = None,
        session_id: str = None,
        model_name: Optional[str] = None,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Process conversation and generate agent response.
        
        Args:
            conversation_history: Complete conversation history (all messages)
            composition_json: Current composition state as JSON string
            media_library: List of media items with name, url, and type
            duration: Total composition duration
            user_id: User ID for logging
            session_id: Session ID for logging
            model_name: Optional model override
            temperature: Generation temperature
        
        Returns:
            Dictionary with type, content, and optional action fields
        """
        logger.info(f"Agent chat request from user={user_id}, session={session_id}")
        logger.info(f"Processing conversation with {len(conversation_history) if conversation_history else 0} messages")
        
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
            
            # Add media library context with names (not URLs)
            if media_library:
                media_list = "\n".join([
                    f'- "{media["name"]}": {media["type"]} ({media.get("duration", "N/A")}s)'
                    for media in media_library
                ])
                context_parts.append(f"**Available Media Files:**\n{media_list}\n\n**IMPORTANT: For probe requests, use the exact name in double quotes (e.g., fileName: \"Beach Video (2)\"). Frontend will resolve names to URLs.**")
            else:
                context_parts.append("**Available Media Files:** No media files in library")
            
            # Add duration context
            if duration is not None:
                context_parts.append(f"**Composition Duration:** {duration} seconds")
            
            # Combine dynamic context (goes in first user message to preserve cache)
            full_context = "\n\n".join(context_parts)
            
            # Call chat provider with structured output schema
            logger.debug("Calling chat provider for agent response...")
            from services.base.ChatProvider import ChatMessage
            
            # Build messages array: static system prompt ONLY (cached) + conversation with dynamic context
            messages = [
                ChatMessage(role="system", content=system_prompt)
            ]
            
            # Add conversation history as actual message turns
            # IMPORTANT: Prepend dynamic context to the FIRST user message to avoid cache invalidation
            if conversation_history:
                logger.info(f"📚 Adding {len(conversation_history)} conversation messages as actual message turns")
                for i, msg in enumerate(conversation_history):
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    
                    # Prepend context to the first user message
                    if i == 0 and role == 'user':
                        content = f"{full_context}\n\n---\n\n{content}"
                        logger.debug(f"  Prepended dynamic context to first user message")
                    
                    messages.append(ChatMessage(role=role, content=content))
                    logger.debug(f"  Added {role} message: {content[:80]}...")
            else:
                logger.warning("⚠️ No conversation history provided - this is unusual")
            
            logger.info(f"🤖 Sending {len(messages)} total messages to AI (1 system + {len(messages)-1} conversation)")
            
            # Save EXACTLY what we're sending to the AI to a file for debugging
            from pathlib import Path
            from datetime import datetime
            
            logs_dir = Path(__file__).parent.parent / "logs"
            logs_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = logs_dir / f"ai_request_{session_id}_{timestamp}.json"
            
            # Convert messages to serializable format
            messages_for_log = []
            for i, msg in enumerate(messages):
                messages_for_log.append({
                    "index": i,
                    "role": msg.role,
                    "content": msg.content if msg.role != "system" else "(static system prompt - cached)",
                    "content_length": len(msg.content)
                })
            
            import json
            with open(log_file, "w") as f:
                json.dump({
                    "user_id": user_id,
                    "session_id": session_id,
                    "timestamp": timestamp,
                    "total_messages": len(messages),
                    "note": "Dynamic context (composition, media library, duration) prepended to first user message to preserve cache",
                    "messages_sent_to_ai": messages_for_log,
                    "system_prompt_static": messages[0].content if messages and messages[0].role == "system" else None,
                    "conversation_messages": [
                        {"role": msg.role, "content": msg.content}
                        for msg in messages[1:] if msg.role != "system"
                    ]
                }, f, indent=2)
            
            logger.info(f"💾 Saved exact AI request to: {log_file}")
            
            # Define strict response schema for Gemini
            response_schema = {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["info", "chat", "edit", "probe", "generate", "fetch"],
                        "description": "The action type for this response"
                    },
                    "content": {
                        "type": "string",
                        "description": "The main message content to display to the user"
                    },
                    "fileName": {
                        "type": "string",
                        "description": "For probe type: the exact name from the media library (e.g., \"Beach Video (2)\"). Frontend resolves names to URLs automatically.",
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
            # Write a paired response log for correlation with the request
            try:
                ai_response_log = logs_dir / f"ai_response_{session_id}_{timestamp}.json"
                response_for_log = {
                    "user_id": user_id,
                    "session_id": session_id,
                    "timestamp": timestamp,
                    "request_log_file": str(log_file),
                    "response": agent_response,
                    "metadata": {
                        "model_used": agent_response.get("metadata", {}).get("model_used") or (model_name or "gemini-2.0-flash-exp"),
                        "message_count": len(messages)
                    }
                }
                with open(ai_response_log, "w") as f:
                    json.dump(response_for_log, f, indent=2)
                logger.info(f"💾 Saved AI response log to: {ai_response_log}")
            except Exception as log_err:
                logger.warning(f"Could not write ai_response log: {log_err}")
            
            # Emit explicit probe details to logs for quick forensics
            if agent_response.get("type") == "probe":
                logger.info(
                    "Probe emission: fileName=%s | question=%s",
                    agent_response.get("fileName"),
                    (agent_response.get("question") or "")[:200]
                )
                
                # Ensure probe responses have content field for validation
                if not agent_response.get("content"):
                    file_name = agent_response.get("fileName", "media")
                    agent_response["content"] = f"Analyzing {file_name}..."
                    logger.debug(f"Added default content for probe response: {agent_response['content']}")
            
            # Validate response type
            valid_types = ["info", "chat", "edit", "probe", "generate", "fetch"]
            if agent_response.get("type") not in valid_types:
                logger.warning(f"Invalid response type: {agent_response.get('type')}, defaulting to 'chat'")
                agent_response["type"] = "chat"
            
            # Add metadata placeholder (token usage would come from model if available)
            if "metadata" not in agent_response:
                agent_response["metadata"] = {
                    "model_used": model_name or "gemini-2.0-flash-exp"
                }
            
            return agent_response
        
        except Exception as e:
            logger.error(f"Unexpected error in agent chat: {str(e)}", exc_info=True)
            return {
                "type": "chat",
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
                "info": "Informational messages, workflow continues automatically",
                "chat": "Conversational messages requiring user input, workflow pauses",
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
                "2. Agent creates detailed plan (type: chat)",
                "3. User confirms plan",
                "4. Agent executes with instructions (type: edit)",
                "5. Implementation processes edit",
                "6. Repeat as needed"
            ]
        }
