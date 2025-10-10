"""
Google Gemini implementation of ChatProvider.

This module provides a fully self-contained implementation of the ChatProvider
interface using Google's Gemini API. All API initialization, configuration, and
calls are handled internally.
"""

import json
import logging
from typing import List, Dict, Any, AsyncIterator, Optional
import google.generativeai as genai
from google.generativeai.types import GenerationConfig, HarmCategory, HarmBlockThreshold

from services.base.ChatProvider import ChatProvider, ChatMessage, ChatResponse


# Configure logging
logger = logging.getLogger(__name__)


class GeminiChatProvider(ChatProvider):
    """
    Google Gemini implementation of the ChatProvider interface.
    
    This provider is fully self-contained and handles all Gemini API interactions
    internally, including configuration, authentication, and error handling.
    
    Attributes:
        api_key: Google AI API key for authentication
        model_name: Name of the Gemini model to use (default: gemini-2.5-flash)
        default_temperature: Default temperature for generation (default: 0.7)
    """
    
    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.5-flash",
        default_temperature: float = 0.7
    ):
        """
        Initialize the Gemini chat provider.
        
        Args:
            api_key: Google AI API key
            model_name: Gemini model to use (gemini-1.5-pro, gemini-1.5-flash, etc.)
            default_temperature: Default temperature for generation
            
        Raises:
            ValueError: If api_key is empty or invalid
        """
        if not api_key:
            raise ValueError("API key is required for GeminiChatProvider")
        
        self.api_key = api_key
        self.model_name = model_name
        self.default_temperature = default_temperature
        
        # Configure the Gemini API
        genai.configure(api_key=self.api_key)
        
        # Initialize the model
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        logger.info(f"GeminiChatProvider initialized with model: {model_name}")
    
    def _convert_messages_to_gemini_format(
        self,
        messages: List[ChatMessage]
    ) -> List[Dict[str, str]]:
        """
        Convert ChatMessage list to Gemini's expected format.
        
        Gemini expects messages in the format:
        [{"role": "user", "parts": ["text"]}, {"role": "model", "parts": ["text"]}]
        
        Args:
            messages: List of ChatMessage objects
            
        Returns:
            List of messages in Gemini format
        """
        gemini_messages = []
        
        for msg in messages:
            # Convert role names
            role = "model" if msg.role == "assistant" else msg.role
            
            gemini_messages.append({
                "role": role,
                "parts": [msg.content]
            })
        
        return gemini_messages
    
    def _extract_system_message(
        self,
        messages: List[ChatMessage]
    ) -> tuple[Optional[str], List[ChatMessage]]:
        """
        Extract system message from the message list.
        
        Gemini handles system messages differently - they're passed as
        system_instruction separately, not in the message history.
        
        Args:
            messages: List of ChatMessage objects
            
        Returns:
            Tuple of (system_instruction, remaining_messages)
        """
        system_instruction = None
        remaining_messages = []
        
        for msg in messages:
            if msg.role == "system":
                # Combine multiple system messages if present
                if system_instruction:
                    system_instruction += "\n\n" + msg.content
                else:
                    system_instruction = msg.content
            else:
                remaining_messages.append(msg)
        
        return system_instruction, remaining_messages
    
    async def generate_chat_response(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatResponse:
        """
        Generate a single chat response using Gemini.
        
        Args:
            messages: List of conversation messages
            temperature: Controls randomness (0.0-2.0)
            max_tokens: Maximum tokens in response (None = use default)
            **kwargs: Additional Gemini-specific parameters
            
        Returns:
            ChatResponse with generated content
            
        Raises:
            ValueError: If messages are invalid or empty
            RuntimeError: If Gemini API call fails
        """
        if not messages:
            raise ValueError("Messages list cannot be empty")
        
        try:
            # Extract system message if present
            system_instruction, conversation_messages = self._extract_system_message(messages)
            
            # Create model with system instruction if present
            if system_instruction:
                model = genai.GenerativeModel(
                    model_name=self.model_name,
                    system_instruction=system_instruction,
                    safety_settings={
                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                    }
                )
            else:
                model = self.model
            
            # Convert messages to Gemini format
            gemini_messages = self._convert_messages_to_gemini_format(conversation_messages)
            
            # Create generation config
            config_params = {
                'temperature': temperature,
                **kwargs
            }
            if max_tokens is not None:
                config_params['max_output_tokens'] = max_tokens
            
            generation_config = GenerationConfig(**config_params)
            
            # Start chat session
            chat = model.start_chat(history=gemini_messages[:-1])
            
            # Send the last message and get response
            response = await chat.send_message_async(
                gemini_messages[-1]["parts"][0],
                generation_config=generation_config
            )
            
            # Extract usage statistics if available
            usage = None
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                usage = {
                    'prompt_tokens': response.usage_metadata.prompt_token_count,
                    'completion_tokens': response.usage_metadata.candidates_token_count,
                    'total_tokens': response.usage_metadata.total_token_count
                }
            
            # Extract metadata
            metadata = {
                'finish_reason': response.candidates[0].finish_reason.name if response.candidates else None,
                'safety_ratings': [
                    {
                        'category': rating.category.name,
                        'probability': rating.probability.name
                    }
                    for rating in response.candidates[0].safety_ratings
                ] if response.candidates else []
            }
            
            logger.info(f"Generated chat response with {usage['total_tokens'] if usage else 'unknown'} tokens")
            
            return ChatResponse(
                content=response.text,
                model=self.model_name,
                usage=usage,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Failed to generate chat response: {str(e)}")
            raise RuntimeError(f"Gemini API call failed: {str(e)}") from e
    
    async def stream_chat_response(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream chat response chunks as they are generated.
        
        Args:
            messages: List of conversation messages
            temperature: Controls randomness (0.0-2.0)
            max_tokens: Maximum tokens in response (None = use default)
            **kwargs: Additional Gemini-specific parameters
            
        Yields:
            Text chunks as they are generated
            
        Raises:
            ValueError: If messages are invalid or empty
            RuntimeError: If Gemini API call fails
        """
        if not messages:
            raise ValueError("Messages list cannot be empty")
        
        try:
            # Extract system message if present
            system_instruction, conversation_messages = self._extract_system_message(messages)
            
            # Create model with system instruction if present
            if system_instruction:
                model = genai.GenerativeModel(
                    model_name=self.model_name,
                    system_instruction=system_instruction,
                    safety_settings={
                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                    }
                )
            else:
                model = self.model
            
            # Convert messages to Gemini format
            gemini_messages = self._convert_messages_to_gemini_format(conversation_messages)
            
            # Create generation config
            config_params = {
                'temperature': temperature,
                **kwargs
            }
            if max_tokens is not None:
                config_params['max_output_tokens'] = max_tokens
            
            generation_config = GenerationConfig(**config_params)
            
            # Start chat session
            chat = model.start_chat(history=gemini_messages[:-1])
            
            # Send the last message and stream response
            response = await chat.send_message_async(
                gemini_messages[-1]["parts"][0],
                generation_config=generation_config,
                stream=True
            )
            
            # Yield chunks as they arrive
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
            
            logger.info("Completed streaming chat response")
            
        except Exception as e:
            logger.error(f"Failed to stream chat response: {str(e)}")
            raise RuntimeError(f"Gemini API streaming failed: {str(e)}") from e
    
    async def generate_chat_response_with_schema(
        self,
        messages: List[ChatMessage],
        response_schema: Dict[str, Any],
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a structured response matching a JSON schema.
        
        Args:
            messages: List of conversation messages
            response_schema: JSON schema defining expected response structure
            temperature: Controls randomness (0.0-2.0)
            **kwargs: Additional Gemini-specific parameters
            
        Returns:
            Dictionary matching the provided schema
            
        Raises:
            ValueError: If messages or schema are invalid
            RuntimeError: If API call fails or response doesn't match schema
        """
        if not messages:
            raise ValueError("Messages list cannot be empty")
        if not response_schema:
            raise ValueError("Response schema cannot be empty")
        
        try:
            # Extract system message if present
            system_instruction, conversation_messages = self._extract_system_message(messages)
            
            # Create model with system instruction if present
            if system_instruction:
                model = genai.GenerativeModel(
                    model_name=self.model_name,
                    system_instruction=system_instruction,
                    safety_settings={
                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                    }
                )
            else:
                model = self.model
            
            # Convert messages to Gemini format
            gemini_messages = self._convert_messages_to_gemini_format(conversation_messages)
            
            # Create generation config with response schema
            generation_config = GenerationConfig(
                temperature=temperature,
                response_mime_type="application/json",
                response_schema=response_schema,
                **kwargs
            )
            
            # Start chat session
            chat = model.start_chat(history=gemini_messages[:-1])
            
            # Send the last message and get response
            response = await chat.send_message_async(
                gemini_messages[-1]["parts"][0],
                generation_config=generation_config
            )
            
            # Parse JSON response
            try:
                structured_response = json.loads(response.text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {response.text}")
                raise RuntimeError(f"Response is not valid JSON: {str(e)}") from e
            
            logger.info("Generated structured response matching schema")
            
            return structured_response
            
        except Exception as e:
            logger.error(f"Failed to generate structured response: {str(e)}")
            raise RuntimeError(f"Gemini structured generation failed: {str(e)}") from e
    
    async def count_tokens(
        self,
        messages: List[ChatMessage],
        **kwargs
    ) -> int:
        """
        Count tokens in a list of messages.
        
        Args:
            messages: List of conversation messages
            **kwargs: Additional Gemini-specific parameters
            
        Returns:
            Approximate token count
            
        Raises:
            ValueError: If messages are invalid
        """
        if not messages:
            raise ValueError("Messages list cannot be empty")
        
        try:
            # Convert messages to single text for counting
            text_content = "\n".join([f"{msg.role}: {msg.content}" for msg in messages])
            
            # Use Gemini's token counting API
            token_count = self.model.count_tokens(text_content)
            
            logger.debug(f"Counted {token_count.total_tokens} tokens in messages")
            
            return token_count.total_tokens
            
        except Exception as e:
            logger.error(f"Failed to count tokens: {str(e)}")
            raise ValueError(f"Token counting failed: {str(e)}") from e
