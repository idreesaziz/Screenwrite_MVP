"""Anthropic Claude implementation of ChatProvider."""

import json
import logging
import os
from typing import List, Dict, Any, AsyncIterator, Optional
from anthropic import AsyncAnthropic
from anthropic.types import Message, MessageParam, TextBlock, ToolUseBlock

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
        default_max_tokens: int = 8192,
        default_thinking_budget: int = 8000
    ):
        """
        Initialize Anthropic client.
        
        Args:
            api_key: Anthropic API key (optional, will use env var if not provided)
            default_model_name: Default model to use
            default_temperature: Default temperature (0.0-1.0)
            default_max_tokens: Default max tokens for response
            default_thinking_budget: Default thinking budget (extended thinking tokens)
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY') or os.getenv('CLAUDE_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY or CLAUDE_API_KEY environment variable is required")
        
        self.default_model_name = default_model_name
        self.default_temperature = default_temperature
        self.default_max_tokens = default_max_tokens
        self.default_thinking_budget = default_thinking_budget
        
        self.client = AsyncAnthropic(api_key=self.api_key)
        logger.info(f"Initialized Anthropic client with model: {default_model_name}")
    
    def _convert_messages(self, messages: List[ChatMessage]) -> tuple[Optional[str], List[MessageParam]]:
        """
        Convert ChatMessage list to Claude format.
        
        Claude expects:
        - system: separate system parameter (not in messages)
        - messages: list of user/assistant messages
        
        Returns:
            (system_prompt, messages_list)
        """
        system_prompt = None
        claude_messages = []
        
        for msg in messages:
            if msg.role == "system":
                # Combine multiple system messages
                system_prompt = msg.content if not system_prompt else system_prompt + "\n\n" + msg.content
            else:
                # Claude uses "user" and "assistant" roles directly
                claude_messages.append({
                    "role": msg.role if msg.role in ["user", "assistant"] else "user",
                    "content": msg.content
                })
        
        return system_prompt, claude_messages
    
    async def generate_chat_response(
        self,
        messages: List[ChatMessage],
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        thinking_budget: Optional[int] = None,
        **kwargs
    ) -> ChatResponse:
        """Generate a single chat response from Claude."""
        if not messages:
            raise ValueError("Messages cannot be empty")
        
        system_prompt, claude_messages = self._convert_messages(messages)
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
        
        if system_prompt:
            request_params["system"] = system_prompt
        
        # Add extended thinking if thinking budget > 0
        # Claude 4.5 and later support extended thinking
        if think > 0 and ("claude-4" in model.lower() or "claude-3-5" in model.lower()):
            request_params["thinking"] = {
                "type": "enabled",
                "budget_tokens": think
            }
        
        response = await self.client.messages.create(**request_params)
        
        # Extract text from response
        content_text = ""
        for block in response.content:
            if isinstance(block, TextBlock):
                content_text += block.text
        
        # Build usage dict
        usage = None
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            }
        
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
        """Stream chat response chunks from Claude."""
        if not messages:
            raise ValueError("Messages cannot be empty")
        
        system_prompt, claude_messages = self._convert_messages(messages)
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
        
        if system_prompt:
            request_params["system"] = system_prompt
        
        async with self.client.messages.stream(**request_params) as stream:
            async for text in stream.text_stream:
                yield text
    
    def _convert_schema_to_text(self, schema: Dict[str, Any], indent_level: int = 0) -> str:
        """
        Recursively convert JSON Schema to natural language instructions for Claude.
        
        Performs full traversal of the schema tree to generate comprehensive format instructions.
        """
        indent = "  " * indent_level
        lines = []
        
        schema_type = schema.get("type")
        description = schema.get("description", "")
        
        if schema_type == "object":
            properties = schema.get("properties", {})
            required_fields = schema.get("required", [])
            
            if properties:
                lines.append(f"{indent}object with properties:")
                for prop_name, prop_schema in properties.items():
                    is_required = "(required)" if prop_name in required_fields else "(optional)"
                    lines.append(f"{indent}  • {prop_name} {is_required}")
                    
                    # Recursively process property schema
                    prop_lines = self._convert_schema_to_text(prop_schema, indent_level + 2)
                    if prop_lines:
                        lines.append(prop_lines)
        
        elif schema_type == "array":
            lines.append(f"{indent}array")
            if description:
                lines.append(f"{indent}  Description: {description}")
            
            if "items" in schema:
                lines.append(f"{indent}  Each item is:")
                item_lines = self._convert_schema_to_text(schema["items"], indent_level + 2)
                if item_lines:
                    lines.append(item_lines)
        
        elif schema_type == "string":
            enum_values = schema.get("enum")
            if enum_values:
                lines.append(f"{indent}string - one of: {', '.join(enum_values)}")
            else:
                lines.append(f"{indent}string")
            
            if description:
                lines.append(f"{indent}  Description: {description}")
        
        elif schema_type == "number" or schema_type == "integer":
            constraints = []
            if "minimum" in schema:
                constraints.append(f"minimum: {schema['minimum']}")
            if "maximum" in schema:
                constraints.append(f"maximum: {schema['maximum']}")
            
            constraint_str = f" ({', '.join(constraints)})" if constraints else ""
            lines.append(f"{indent}{schema_type}{constraint_str}")
            
            if description:
                lines.append(f"{indent}  Description: {description}")
        
        elif schema_type == "boolean":
            lines.append(f"{indent}boolean")
            if description:
                lines.append(f"{indent}  Description: {description}")
        
        return "\n".join(lines)
    
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
        Generate a structured response matching a JSON schema using Claude's recommended approach.
        
        Following Claude's documentation:
        1. Convert schema to natural language instructions
        2. Add instructions to system prompt
        3. Prefill assistant response with opening brace
        4. Parse the completed JSON response
        """
        if not messages or not response_schema:
            raise ValueError("Messages and schema required")
        
        system_prompt, claude_messages = self._convert_messages(messages)
        model = model_name or self.default_model_name
        temp = temperature if temperature is not None else self.default_temperature
        think = thinking_budget if thinking_budget is not None else self.default_thinking_budget
        
        # Convert schema to Claude-friendly text instructions
        schema_instructions = self._convert_schema_to_text(response_schema)
        
        # Enhance system prompt with schema instructions
        enhanced_system = (system_prompt or "") + f"\n\nYou must respond with valid JSON matching this exact structure:\n\n{schema_instructions}\n\nRespond with ONLY valid JSON, no explanations or markdown formatting."
        
        # Prefill assistant response with opening brace
        prefilled_messages = claude_messages + [{"role": "assistant", "content": "{"}]
        
        request_params = {
            "model": model,
            "messages": prefilled_messages,
            "system": enhanced_system,
            "temperature": temp,
            "max_tokens": 8192,  # Structured output may need more tokens
            **kwargs
        }
        
        # Add extended thinking if thinking budget > 0
        if think > 0 and ("claude-4" in model.lower() or "claude-3-5" in model.lower()):
            request_params["thinking"] = {
                "type": "enabled",
                "budget_tokens": think
            }
        
        response = await self.client.messages.create(**request_params)
        
        # Extract text content from response
        response_text = ""
        for block in response.content:
            if isinstance(block, TextBlock):
                response_text += block.text
        
        # Prepend the opening brace we prefilled and parse
        full_json = "{" + response_text
        
        try:
            return json.loads(full_json)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude's JSON response: {e}")
            logger.error(f"Response text: {full_json[:500]}...")
            raise RuntimeError(f"Claude did not return valid JSON: {e}")
    
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
