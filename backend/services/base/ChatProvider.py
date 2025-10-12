"""
Abstract base class for chat/LLM providers.

This module defines the contract that all chat provider implementations must follow.
It provides a consistent interface for different LLM services (Gemini, GPT, Claude, etc.).
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncIterator, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ChatMessage:
    """
    Represents a single message in a conversation.
    
    Attributes:
        role: The role of the message sender ('user', 'assistant', 'system')
        content: The text content of the message
        metadata: Optional additional data (timestamps, tokens, etc.)
    """
    role: str  # 'user', 'assistant', 'system'
    content: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ChatResponse:
    """
    Represents a response from a chat provider.
    
    Attributes:
        content: The generated text response
        model: The name/ID of the model that generated the response
        usage: Token usage statistics (prompt_tokens, completion_tokens, total_tokens)
        metadata: Optional additional data (finish_reason, safety_ratings, etc.)
        timestamp: When the response was generated
    """
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)


class ChatProvider(ABC):
    """
    Abstract base class for chat/LLM providers.
    
    All chat provider implementations (Gemini, GPT, Claude, etc.) must implement
    these methods to provide a consistent interface across different LLM services.
    """
    
    @abstractmethod
    async def generate_chat_response(
        self,
        messages: List[ChatMessage],
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatResponse:
        """
        Generate a single chat response from the provider.
        
        Args:
            messages: List of conversation messages
            model_name: Override default model (None = use provider's default)
            temperature: Controls randomness (0.0 = deterministic, 1.0 = creative)
            max_tokens: Maximum tokens in the response (None = provider default)
            **kwargs: Provider-specific parameters
            
        Returns:
            ChatResponse with generated content and metadata
            
        Raises:
            ValueError: If messages are invalid or empty
            RuntimeError: If API call fails
        """
        pass
    
    @abstractmethod
    async def stream_chat_response(
        self,
        messages: List[ChatMessage],
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream chat response chunks as they are generated.
        
        Args:
            messages: List of conversation messages
            model_name: Override default model (None = use provider's default)
            temperature: Controls randomness (0.0 = deterministic, 1.0 = creative)
            max_tokens: Maximum tokens in the response (None = provider default)
            **kwargs: Provider-specific parameters
            
        Yields:
            Text chunks as they are generated
            
        Raises:
            ValueError: If messages are invalid or empty
            RuntimeError: If API call fails
        """
        pass
    
    @abstractmethod
    async def generate_chat_response_with_schema(
        self,
        messages: List[ChatMessage],
        response_schema: Dict[str, Any],
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a structured response matching a JSON schema.
        
        This method forces the LLM to return a response that conforms to the
        provided JSON schema, useful for structured data extraction or generation.
        
        Args:
            messages: List of conversation messages
            response_schema: JSON schema defining the expected response structure
            model_name: Override default model (None = use provider's default)
            temperature: Controls randomness (0.0 = deterministic, 1.0 = creative)
            **kwargs: Provider-specific parameters
            
        Returns:
            Dictionary matching the provided schema
            
        Raises:
            ValueError: If messages or schema are invalid
            RuntimeError: If API call fails or response doesn't match schema
        """
        pass
    
    @abstractmethod
    async def count_tokens(
        self,
        messages: List[ChatMessage],
        **kwargs
    ) -> int:
        """
        Count tokens in a list of messages without generating a response.
        
        Useful for checking if messages fit within model limits before making
        an API call.
        
        Args:
            messages: List of conversation messages
            **kwargs: Provider-specific parameters
            
        Returns:
            Approximate token count
            
        Raises:
            ValueError: If messages are invalid
        """
        pass
