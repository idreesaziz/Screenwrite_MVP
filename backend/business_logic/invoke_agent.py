"""
Agent Service - Business Logic Layer.

Orchestrates conversational AI agent interactions for video editing assistance.
"""

import logging
import json
from typing import Optional, List, Dict, Any

from services.base.ChatProvider import ChatProvider
from prompts.agent_prompts import build_agent_system_prompt
from rag.llm_selector import select_example

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
            # Build static system prompt base (will be cached by provider)
            system_prompt_base = build_agent_system_prompt()
            
            # Retrieve relevant example using LLM-based RAG
            retrieved_example = None
            retrieved_filename = None
            if conversation_history:
                logger.info(f"🔍 Using LLM to select relevant example from conversation...")
                
                try:
                    result = await select_example(conversation_history)
                    if result:
                        retrieved_example = result['content']
                        retrieved_filename = result['filename']
                        confidence = result.get('confidence', 'unknown')
                        reasoning = result.get('reasoning', '')
                        logger.info(f"✓ Selected example: {retrieved_filename} (confidence: {confidence})")
                        logger.info(f"  Reasoning: {reasoning}")
                    else:
                        logger.info("No relevant example found for this conversation")
                except Exception as e:
                    logger.error(f"Error during LLM-based RAG: {e}")
                    logger.info("Continuing without RAG example")
            
            # Append RAG example to system prompt (cached, not in conversation)
            system_prompt = system_prompt_base
            if retrieved_example:
                system_prompt += f"\n\n---\n\n# REFERENCE EXAMPLE FOR AGENTIC BEHAVIOR\n\nThe following example from '{retrieved_filename}' demonstrates the agentic workflow pattern you should follow. Study how it progresses through steps autonomously. Use this as a behavioral guide, but adapt the specific actions to the current user request.\n\n{retrieved_example}\n\n---\n\nNow proceed with the actual conversation below, following the agentic pattern demonstrated in the example above."
                logger.info(f"📎 Appended RAG example ({retrieved_filename}) to system prompt for caching")
            
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
            from datetime import datetime
            context_timestamp = datetime.utcnow().isoformat() + "Z"
            context_message_content = f"CURRENT PROJECT SNAPSHOT @ {context_timestamp}\n\n{full_context}"
            
            # Call chat provider with structured output schema
            logger.debug("Calling chat provider for agent response...")
            from services.base.ChatProvider import ChatMessage
            
            # Build messages array: static system prompt ONLY (cached) + conversation with dynamic context
            messages = [
                ChatMessage(role="system", content=system_prompt)
            ]
            messages.append(ChatMessage(role="system", content=context_message_content))
            
            # Add conversation history as actual message turns
            # Dynamic context prepended ONLY to first user message (composition, media library)
            if conversation_history:
                logger.info(f"📚 Adding {len(conversation_history)} conversation messages as actual message turns")
                for i, msg in enumerate(conversation_history):
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
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
                    "content": msg.content if not (msg.role == "system" and i == 0) else "(static system prompt - cached)",
                    "content_length": len(msg.content)
                })
            
            import json
            with open(log_file, "w") as f:
                json.dump({
                    "user_id": user_id,
                    "session_id": session_id,
                    "timestamp": timestamp,
                    "total_messages": len(messages),
                    "note": "RAG example appended to system prompt (cached). Dynamic context prepended to first user message only.",
                    "rag_example_used": retrieved_filename if retrieved_example else None,
                    "messages_sent_to_ai": messages_for_log,
                    "system_prompt_static": messages[0].content if messages and messages[0].role == "system" else None,
                    "conversation_messages": [
                        {
                            "role": msg.role,
                            "content": msg.content if not (idx == 0 and msg.role == "system") else "(static system prompt - cached)"
                        }
                        for idx, msg in enumerate(messages)
                        if not (msg.role == "system" and idx == 0)
                    ]
                }, f, indent=2)
            
            logger.info(f"💾 Saved exact AI request to: {log_file}")
            
            # Define strict response schema for Gemini
            response_schema = {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["info", "sleep", "edit", "probe", "generate", "fetch"],
                        "description": "The action type for this response"
                    },
                    "content": {
                        "type": "string",
                        "description": "The main message content to display to the user"
                    },
                    "files": {
                        "type": "array",
                        "description": "For probe type: array of media files to analyze (images, videos, audio, YouTube URLs)",
                        "items": {
                            "type": "object",
                            "properties": {
                                "fileName": {
                                    "type": "string",
                                    "description": "Exact name from media library (e.g., \"Beach Video (2)\") or full URL"
                                },
                                "question": {
                                    "type": "string",
                                    "description": "Question to ask about this specific file"
                                }
                            },
                            "required": ["fileName", "question"]
                        },
                        "nullable": True
                    },
                    "fileName": {
                        "type": "string",
                        "description": "For probe type (legacy single file): the exact name from the media library (e.g., \"Beach Video (2)\"). Frontend resolves names to URLs automatically.",
                        "nullable": True
                    },
                    "question": {
                        "type": "string",
                        "description": "For probe type (legacy single file): question to ask about the media",
                        "nullable": True
                    },
                    "content_type": {
                        "type": "string",
                        "enum": ["image", "video", "logo", "audio"],
                        "description": "For generate type: type of media to generate. Use 'logo' for transparent logos with simple prompts, 'audio' for voice-over narration with text scripts",
                        "nullable": True
                    },
                    "prompt": {
                        "type": "string",
                        "description": "For generate type: generation prompt. For images/videos, use detailed descriptions. For logos, use simple 2-5 word descriptions. For audio, provide the complete text script to be spoken.",
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
                    "voice_settings": {
                        "type": "object",
                        "description": "For audio generation: voice configuration using Gemini 2.5 Pro TTS. voice_id: Gemini voice name like 'Aoede' (female, warm), 'Charon' (male, professional), 'Kore' (female, versatile). language_code: e.g., 'en-US'. style_prompt: Optional delivery style like 'Speak dramatically with urgency', 'Whisper quietly [whispering]', 'Sound excited and energetic'. Optional: speaking_rate (0.25-4.0), pitch (-20 to 20). Example: {\"voice_id\": \"Aoede\", \"language_code\": \"en-US\", \"style_prompt\": \"Speak with confidence and authority\"}",
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
                # Support both batch (files array) and legacy single file format
                if agent_response.get("files"):
                    file_count = len(agent_response.get("files", []))
                    file_names = [f.get("fileName", "unknown") for f in agent_response.get("files", [])]
                    logger.info(
                        "Batch probe emission: %d files | fileNames=%s",
                        file_count,
                        ", ".join(file_names)
                    )
                    
                    # Validate each file has required fields
                    for i, file_obj in enumerate(agent_response.get("files", [])):
                        if not file_obj.get("fileName"):
                            logger.error(f"File {i} missing fileName: {file_obj}")
                        if not file_obj.get("question"):
                            logger.warning(f"File {i} missing question, using default")
                            file_obj["question"] = "Describe what you see in this media."
                else:
                    logger.info(
                        "Single probe emission: fileName=%s | question=%s",
                        agent_response.get("fileName"),
                        (agent_response.get("question") or "")[:200]
                    )
                
                # Ensure probe responses have content field for validation
                if not agent_response.get("content"):
                    if agent_response.get("files"):
                        file_count = len(agent_response.get("files", []))
                        agent_response["content"] = f"Analyzing {file_count} file(s)..."
                    else:
                        file_name = agent_response.get("fileName", "media")
                        agent_response["content"] = f"Analyzing {file_name}..."
                    logger.debug(f"Added default content for probe response: {agent_response['content']}")
            
            # Validate response type
            valid_types = ["info", "sleep", "edit", "probe", "generate", "fetch"]
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
                "info": "Informational messages, workflow continues automatically",
                "chat": "Conversational messages requiring user input, workflow pauses",
                "edit": "Direct editing instructions for composition changes",
                "probe": "Media content analysis requests",
                "generate": "Media generation requests (images: 16:9 1920x1080, videos: 8s 16:9 1920x1080, logos: 1:1 transparent PNG, audio: voice-over narration)",
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
