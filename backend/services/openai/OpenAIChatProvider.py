"""OpenAI implementation of ChatProvider."""

import json
import logging
import os
from typing import List, Dict, Any, AsyncIterator, Optional
from openai import AsyncOpenAI

from services.base.ChatProvider import ChatProvider, ChatMessage, ChatResponse

logger = logging.getLogger(__name__)


class OpenAIChatProvider(ChatProvider):
    """OpenAI implementation using OpenAI API.
    
    Authentication via OPENAI_API_KEY environment variable.
    Supports structured output via response_format and reasoning models.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model_name: str = "gpt-4o-mini",
        default_temperature: float = 1.0,
        default_max_tokens: int = 16384,
        default_reasoning_effort: str = "medium"
    ):
        """
        Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key (optional, will use env var if not provided)
            default_model_name: Default model to use (gpt-4o, gpt-4o-mini, o1, etc.)
            default_temperature: Default temperature (0.0-2.0)
            default_max_tokens: Default max tokens for response
            default_reasoning_effort: For reasoning models (o1): low, medium, high
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.default_model_name = default_model_name
        self.default_temperature = default_temperature
        self.default_max_tokens = default_max_tokens
        self.default_reasoning_effort = default_reasoning_effort
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        logger.info(f"Initialized OpenAI client with model: {default_model_name}")
    
    def _convert_messages(self, messages: List[ChatMessage]) -> List[Dict[str, str]]:
        """
        Convert ChatMessage list to OpenAI format.
        
        OpenAI expects:
        - messages: list of {"role": "system"|"user"|"assistant", "content": "..."}
        
        Returns:
            List of OpenAI message dicts
        """
        openai_messages = []
        
        for msg in messages:
            openai_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return openai_messages
    
    def _is_reasoning_model(self, model: str) -> bool:
        """Check if model is a reasoning model (o1, o3, etc.)."""
        return model.startswith("o1") or model.startswith("o3")
    
    async def generate_chat_response(
        self,
        messages: List[ChatMessage],
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        reasoning_effort: Optional[str] = None,
        **kwargs
    ) -> ChatResponse:
        """Generate a single chat response from OpenAI."""
        if not messages:
            raise ValueError("Messages cannot be empty")
        
        openai_messages = self._convert_messages(messages)
        model = model_name or self.default_model_name
        max_tok = max_tokens or self.default_max_tokens
        
        # Build request parameters
        request_params = {
            "model": model,
            "messages": openai_messages,
            "max_tokens": max_tok,
            **kwargs
        }
        
        # Reasoning models (o1, o3) don't support temperature
        # They use reasoning_effort instead
        if self._is_reasoning_model(model):
            effort = reasoning_effort or self.default_reasoning_effort
            request_params["reasoning_effort"] = effort
        else:
            temp = temperature if temperature is not None else self.default_temperature
            request_params["temperature"] = temp
        
        response = await self.client.chat.completions.create(**request_params)
        
        # Extract content
        content_text = response.choices[0].message.content or ""
        
        # Build usage dict
        usage = None
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            # Add reasoning tokens if present (for o1 models)
            if hasattr(response.usage, 'completion_tokens_details'):
                details = response.usage.completion_tokens_details
                if hasattr(details, 'reasoning_tokens'):
                    usage["reasoning_tokens"] = details.reasoning_tokens
        
        return ChatResponse(
            content=content_text,
            model=response.model,
            usage=usage,
            metadata={
                "finish_reason": response.choices[0].finish_reason,
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
        """Stream chat response chunks from OpenAI."""
        if not messages:
            raise ValueError("Messages cannot be empty")
        
        openai_messages = self._convert_messages(messages)
        model = model_name or self.default_model_name
        temp = temperature if temperature is not None else self.default_temperature
        max_tok = max_tokens or self.default_max_tokens
        
        request_params = {
            "model": model,
            "messages": openai_messages,
            "temperature": temp,
            "max_tokens": max_tok,
            "stream": True,
            **kwargs
        }
        
        stream = await self.client.chat.completions.create(**request_params)
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    async def generate_chat_response_with_schema(
        self,
        messages: List[ChatMessage],
        response_schema: Dict[str, Any],
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        reasoning_effort: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a structured response matching a JSON schema using OpenAI's structured outputs.
        
        OpenAI supports native structured outputs via response_format with json_schema.
        """
        if not messages or not response_schema:
            raise ValueError("Messages and schema required")
        
        openai_messages = self._convert_messages(messages)
        model = model_name or self.default_model_name
        
        # Wrap schema in OpenAI's format
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "structured_response",
                "strict": True,
                "schema": response_schema
            }
        }
        
        request_params = {
            "model": model,
            "messages": openai_messages,
            "response_format": response_format,
            **kwargs
        }
        
        # Reasoning models (o1, o3) handle parameters differently
        if self._is_reasoning_model(model):
            effort = reasoning_effort or self.default_reasoning_effort
            request_params["reasoning_effort"] = effort
        else:
            temp = temperature if temperature is not None else self.default_temperature
            request_params["temperature"] = temp
        
        response = await self.client.chat.completions.create(**request_params)
        
        # Parse JSON response
        content_text = response.choices[0].message.content or "{}"
        return json.loads(content_text)
    
    async def count_tokens(
        self,
        messages: List[ChatMessage],
        model_name: Optional[str] = None,
        **kwargs
    ) -> int:
        """
        Count tokens in messages.
        
        OpenAI doesn't provide a direct token counting API in the SDK.
        We use a rough estimate: ~4 characters per token (similar to GPT tokenization).
        For production, consider using tiktoken library.
        """
        if not messages:
            raise ValueError("Messages cannot be empty")
        
        # Rough estimate: count characters and divide by 4
        total_chars = sum(len(msg.content) for msg in messages)
        return total_chars // 4
