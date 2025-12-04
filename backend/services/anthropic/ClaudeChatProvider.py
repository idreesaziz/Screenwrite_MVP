"""Anthropic Claude implementation of ChatProvider."""

import logging
import os
from typing import List, Dict, Any, AsyncIterator, Optional, Type
from anthropic import AsyncAnthropic
from anthropic.types import TextBlock
import instructor
from pydantic import BaseModel, create_model

from services.base.ChatProvider import ChatProvider, ChatMessage, ChatResponse

logger = logging.getLogger(__name__)


class ClaudeChatProvider(ChatProvider):
    """Claude implementation using Anthropic API.
    
    Authentication via ANTHROPIC_API_KEY or CLAUDE_API_KEY environment variable.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model_name: str = "claude-sonnet-4-5",
        default_temperature: float = 1.0,
        default_max_tokens: int = 16384,
        default_thinking_budget: int = 0
    ):
        """
        Initialize Anthropic client.
        
        Args:
            api_key: Anthropic API key (optional, will use env var if not provided)
            default_model_name: Default model to use
            default_temperature: Default temperature (0.0-1.0)
            default_max_tokens: Default max tokens for response (16K default, Claude Sonnet 4.5 supports up to 64K)
            default_thinking_budget: Default thinking budget (extended thinking tokens, 0 = disabled)
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY') or os.getenv('CLAUDE_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY or CLAUDE_API_KEY environment variable is required")
        
        self.default_model_name = default_model_name
        self.default_temperature = default_temperature
        self.default_max_tokens = default_max_tokens
        self.default_thinking_budget = default_thinking_budget
        
        # Initialize base Anthropic client for standard chat methods
        self.base_client = AsyncAnthropic(api_key=self.api_key)
        
        # Initialize Instructor-wrapped client for structured output methods
        self.client = instructor.from_anthropic(
            AsyncAnthropic(api_key=self.api_key),
            mode=instructor.Mode.ANTHROPIC_TOOLS
        )
        logger.info(f"Initialized Instructor-wrapped Anthropic client with model: {default_model_name}")
    
    def _convert_messages(
        self, 
        messages: List[ChatMessage], 
        enable_caching: bool = True
    ) -> tuple[Optional[List[Dict[str, Any]]], List[Dict[str, Any]]]:
        """
        Convert ChatMessage list to Claude format with optional prompt caching.
        
        Claude expects:
        - system: separate system parameter (can be string or list of content blocks)
        - messages: list of user/assistant messages
        
        When caching is enabled, system prompts are converted to content blocks
        with cache_control for 1-hour TTL.
        
        Returns:
            (system_blocks, messages_list)
        """
        system_content = []
        claude_messages = []
        
        for msg in messages:
            if msg.role == "system":
                # Collect system messages as content blocks
                system_content.append(msg.content)
            else:
                # Map role: tool→assistant (matches Gemini's tool→model pattern)
                # Claude API only accepts "user" or "assistant" roles
                role = "assistant" if msg.role in ["assistant", "tool"] else "user"
                claude_messages.append({
                    "role": role,
                    "content": msg.content
                })
        
        # Convert system content to format with caching
        system_blocks = None
        if system_content:
            combined_system = "\n\n".join(system_content)
            
            if enable_caching:
                # Use content blocks format with cache_control for 1-hour TTL
                # This caches the entire system prompt (including schema instructions)
                system_blocks = [
                    {
                        "type": "text",
                        "text": combined_system,
                        "cache_control": {
                            "type": "ephemeral",
                            "ttl": "1h"
                        }
                    }
                ]
            else:
                # Return as simple string for non-cached requests
                system_blocks = combined_system
        
        return system_blocks, claude_messages
    
    async def generate_chat_response(
        self,
        messages: List[ChatMessage],
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        thinking_budget: Optional[int] = None,
        **kwargs
    ) -> ChatResponse:
        """Generate a single chat response from Claude with 1-hour prompt caching enabled."""
        if not messages:
            raise ValueError("Messages cannot be empty")
        
        system_blocks, claude_messages = self._convert_messages(messages, enable_caching=True)
        model = model_name or self.default_model_name
        temp = temperature if temperature is not None else self.default_temperature
        max_tok = max_tokens or self.default_max_tokens
        think = thinking_budget if thinking_budget is not None else self.default_thinking_budget
        
        # Build request parameters
        request_params = {
            "model": model,
            "messages": claude_messages,
            "temperature": temp,
            "max_tokens": max_tok,
            **kwargs
        }
        
        if system_blocks:
            request_params["system"] = system_blocks
        
        # Add extended thinking if thinking budget > 0
        # Claude 4.5 and later support extended thinking
        if think > 0 and ("claude-4" in model.lower() or "claude-3-5" in model.lower()):
            request_params["thinking"] = {
                "type": "enabled",
                "budget_tokens": think
            }
        
        response = await self.base_client.messages.create(**request_params)
        
        # Extract text from response
        content_text = ""
        for block in response.content:
            if isinstance(block, TextBlock):
                content_text += block.text
        
        # Build usage dict with cache metrics
        usage = None
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            }
            
            # Add cache metrics if available
            if hasattr(response.usage, 'cache_creation_input_tokens'):
                usage["cache_creation_input_tokens"] = response.usage.cache_creation_input_tokens
            if hasattr(response.usage, 'cache_read_input_tokens'):
                usage["cache_read_input_tokens"] = response.usage.cache_read_input_tokens
            
            # Log cache performance (using both logger and print for visibility)
            if hasattr(response.usage, 'cache_read_input_tokens') and response.usage.cache_read_input_tokens > 0:
                msg = f"✅ CACHE HIT! Read {response.usage.cache_read_input_tokens} tokens from cache (90% cost savings!)"
                logger.info(msg)
                print(f"\n{'='*80}\n{msg}\n{'='*80}\n")
            if hasattr(response.usage, 'cache_creation_input_tokens') and response.usage.cache_creation_input_tokens > 0:
                msg = f"📝 Cache write: {response.usage.cache_creation_input_tokens} tokens written to 1-hour cache"
                logger.info(msg)
                print(f"\n{'='*80}\n{msg}\n{'='*80}\n")
        
        return ChatResponse(
            content=content_text,
            model=response.model,
            usage=usage,
            metadata={
                "stop_reason": response.stop_reason,
                "id": response.id
            }
        )
    
    async def stream_chat_response(
        self,
        messages: List[ChatMessage],
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream chat response chunks from Claude with 1-hour prompt caching enabled."""
        if not messages:
            raise ValueError("Messages cannot be empty")
        
        system_blocks, claude_messages = self._convert_messages(messages, enable_caching=True)
        model = model_name or self.default_model_name
        temp = temperature if temperature is not None else self.default_temperature
        max_tok = max_tokens or self.default_max_tokens
        
        request_params = {
            "model": model,
            "messages": claude_messages,
            "temperature": temp,
            "max_tokens": max_tok,
            **kwargs
        }
        
        if system_blocks:
            request_params["system"] = system_blocks
        
        async with self.base_client.messages.stream(**request_params) as stream:
            async for text in stream.text_stream:
                yield text
    
    async def generate_chat_response_with_schema(
        self,
        messages: List[ChatMessage],
        response_schema: Dict[str, Any],
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        thinking_budget: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a structured response matching a JSON schema using Instructor.
        
        Instructor handles:
        - Automatic schema conversion to tool calls
        - Robust JSON parsing with validation
        - Automatic retries on validation failures
        - Clean integration with Pydantic models
        """
        if not messages or not response_schema:
            raise ValueError("Messages and schema required")
        
        # Convert messages with caching enabled
        system_blocks, claude_messages = self._convert_messages(messages, enable_caching=True)
        model = model_name or self.default_model_name
        temp = temperature if temperature is not None else self.default_temperature
        think = thinking_budget if thinking_budget is not None else self.default_thinking_budget
        
        # Create dynamic Pydantic model from JSON schema
        # Extract properties and required fields from schema
        properties = response_schema.get("properties", {})
        required_fields = response_schema.get("required", [])
        
        # Build field definitions for Pydantic
        field_definitions = {}
        for field_name, field_schema in properties.items():
            field_type = self._json_schema_type_to_python(field_schema)
            is_required = field_name in required_fields
            
            if is_required:
                field_definitions[field_name] = (field_type, ...)
            else:
                field_definitions[field_name] = (Optional[field_type], None)
        
        # Create dynamic Pydantic model
        DynamicModel = create_model(
            'DynamicResponseModel',
            **field_definitions
        )
        
        # Build request parameters
        request_params = {
            "model": model,
            "messages": claude_messages,
            "temperature": temp,
            "max_tokens": 16384,
            "response_model": DynamicModel,
            **kwargs
        }
        
        if system_blocks:
            request_params["system"] = system_blocks
        
        # Add extended thinking if thinking budget > 0
        if think > 0 and ("claude-4" in model.lower() or "claude-3-5" in model.lower()):
            request_params["thinking"] = {
                "type": "enabled",
                "budget_tokens": think
            }
        
        # Use Instructor's create_with_completion to get both response and cache stats
        response, completion = await self.client.chat.completions.create_with_completion(
            **request_params
        )
        
        # Log cache performance
        if hasattr(completion.usage, 'cache_read_input_tokens') and completion.usage.cache_read_input_tokens > 0:
            msg = f"✅ CACHE HIT (structured)! Read {completion.usage.cache_read_input_tokens} tokens from cache"
            logger.info(msg)
            print(f"\n{'='*80}\n{msg}\n{'='*80}\n")
        if hasattr(completion.usage, 'cache_creation_input_tokens') and completion.usage.cache_creation_input_tokens > 0:
            msg = f"📝 Cache write (structured): {completion.usage.cache_creation_input_tokens} tokens written to cache"
            logger.info(msg)
            print(f"\n{'='*80}\n{msg}\n{'='*80}\n")
        
        # Convert Pydantic model to dict
        return response.model_dump()
    
    def _json_schema_type_to_python(self, field_schema: Dict[str, Any]) -> type:
        """Convert JSON schema type to Python type for Pydantic."""
        schema_type = field_schema.get("type")
        
        if schema_type == "string":
            return str
        elif schema_type == "integer":
            return int
        elif schema_type == "number":
            return float
        elif schema_type == "boolean":
            return bool
        elif schema_type == "array":
            items_schema = field_schema.get("items", {})
            item_type = self._json_schema_type_to_python(items_schema)
            return List[item_type]
        elif schema_type == "object":
            # For nested objects, use Dict[str, Any]
            return Dict[str, Any]
        else:
            # Default to Any for unknown types
            return Any
    
    async def count_tokens(
        self,
        messages: List[ChatMessage],
        model_name: Optional[str] = None,
        **kwargs
    ) -> int:
        """
        Count tokens in messages.
        
        Note: Anthropic doesn't provide a direct token counting API like OpenAI.
        We use a rough estimate: ~4 characters per token (similar to GPT tokenization).
        For production, consider using tiktoken or anthropic's token counting if available.
        """
        if not messages:
            raise ValueError("Messages cannot be empty")
        
        # Rough estimate: count characters and divide by 4
        total_chars = sum(len(msg.content) for msg in messages)
        return total_chars // 4
