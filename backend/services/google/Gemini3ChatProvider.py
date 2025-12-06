"""Google Gemini 3.0 implementation using Vertex AI with thinking levels."""

import json
import logging
import os
from typing import List, Dict, Any, AsyncIterator, Optional, Literal
from google import genai
from google.genai import types

from services.base.ChatProvider import ChatProvider, ChatMessage, ChatResponse

logger = logging.getLogger(__name__)


class Gemini3ChatProvider(ChatProvider):
    """Gemini 3.0 implementation using Vertex AI (Google Cloud Platform).
    
    Uses thinking_level configuration for Gemini 3 models.
    Supports "low" and "high" thinking levels for controlled reasoning depth.
    
    Authentication is handled via Application Default Credentials (ADC):
    - Service account JSON file via GOOGLE_APPLICATION_CREDENTIALS env var
    - gcloud auth application-default login
    - Workload Identity (for GKE/Cloud Run)
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        location: str = "us-central1",
        default_model_name: str = "gemini-3-pro-preview",
        default_temperature: float = 1.0,
        default_thinking_level: Literal["low", "high"] = "low"
    ):
        """
        Initialize Vertex AI client for Gemini 3.0 models.
        
        Args:
            project_id: Google Cloud project ID (optional, will use from ADC if not provided)
            location: GCP region (default: us-central1)
            default_model_name: Default model to use (gemini-3-pro, gemini-3-pro-preview)
            default_temperature: Default temperature
            default_thinking_level: Default thinking level ("low" or "high")
        
        Authentication:
            Uses Application Default Credentials (ADC) in this order:
            1. GOOGLE_APPLICATION_CREDENTIALS environment variable pointing to service account JSON
            2. gcloud auth application-default login credentials
            3. Workload Identity (in GKE/Cloud Run)
        """
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT')
        self.location = location
        self.default_model_name = default_model_name
        self.default_temperature = default_temperature
        self.default_thinking_level = default_thinking_level
        
        # Determine authentication mode: Vertex AI (ADC) or API Key
        use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() == "true"
        
        if use_vertex or self.project_id:
            # Use Vertex AI with Application Default Credentials
            if not self.project_id:
                raise ValueError("GOOGLE_CLOUD_PROJECT is required for Vertex AI mode")
            
            # Ensure Vertex AI environment variable is set
            os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'True'
            
            # Gemini 3 Pro Preview is only available in global region for now
            if "gemini-3" in self.default_model_name and self.location != "global":
                logger.warning(f"Gemini 3 models require 'global' location. Switching from {self.location} to 'global'.")
                self.location = "global"
                os.environ['GOOGLE_CLOUD_LOCATION'] = 'global'
            
            from google.genai.types import HttpOptions
            self.client = genai.Client(
                http_options=HttpOptions(api_version="v1"),
                location=self.location,
                project=self.project_id
            )
            logger.info(f"Initialized Vertex AI client with Gemini 3 model: {default_model_name}, project: {self.project_id}, location: {self.location}, thinking_level: {default_thinking_level}")
        else:
            # Use Google AI API with API key
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable is required for API key mode")
            
            self.client = genai.Client(api_key=api_key)
            logger.info(f"Initialized Google AI API with API key, Gemini 3 model: {default_model_name}, thinking_level: {default_thinking_level}")
    
    def _convert_messages(self, messages: List[ChatMessage]):
        """
        Convert ChatMessage list to Gemini format.
        
        For agent workflows, conversation history is serialized as plain text
        to bypass alternation requirements. This allows:
        - Consecutive model messages (INFO → ACTION → tool result)
        - Autonomous multi-step workflows
        - Natural agent conversation patterns
        
        Returns:
            (system_instruction, contents)
        """
        system_instruction = None
        conversation_messages = []
        
        # Separate system messages from conversation
        for msg in messages:
            if msg.role == "system":
                system_instruction = msg.content if not system_instruction else system_instruction + "\n\n" + msg.content
            else:
                conversation_messages.append(msg)
        
        # Convert conversation to plain text format (bypasses role alternation)
        if conversation_messages:
            conversation_text = "=== CONVERSATION HISTORY ===\n\n"
            
            for msg in conversation_messages:
                if msg.role == "user":
                    conversation_text += f"USER: {msg.content}\n\n"
                elif msg.role in ["assistant", "tool"]:
                    conversation_text += f"AGENT: {msg.content}\n\n"
            
            conversation_text += "=== END HISTORY ===\n\nGenerate the next AGENT response (ONLY ONE response, not multiple):"
            
            # Return as single user message
            contents = [types.Content(role="user", parts=[types.Part.from_text(text=conversation_text)])]
        else:
            # No conversation yet - should not happen but handle gracefully
            contents = []
        
        return system_instruction, contents
    
    async def generate_chat_response(
        self,
        messages: List[ChatMessage],
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        thinking_level: Optional[Literal["low", "high"]] = None,
        **kwargs
    ) -> ChatResponse:
        if not messages:
            raise ValueError("Messages cannot be empty")
        
        system_inst, contents = self._convert_messages(messages)
        model = model_name or self.default_model_name
        temp = temperature if temperature is not None else self.default_temperature
        think_level = thinking_level if thinking_level is not None else self.default_thinking_level
        
        # Use official ThinkingLevel enum from google.genai.types
        # Low thinking: types.ThinkingLevel.LOW
        # High thinking: types.ThinkingLevel.HIGH
        thinking_level_enum = types.ThinkingLevel.LOW if think_level == "low" else types.ThinkingLevel.HIGH
        
        config_params = {
            'temperature': temp,
            'top_p': 0.95,
            'safety_settings': [
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
            ],
            'thinking_config': types.ThinkingConfig(thinking_level=thinking_level_enum),
            **kwargs
        }
        
        if system_inst:
            config_params['system_instruction'] = system_inst
        
        if max_tokens:
            config_params['max_output_tokens'] = max_tokens
        
        response = self.client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(**config_params)
        )
        
        usage = None
        if hasattr(response, 'usage_metadata'):
            usage = {
                'prompt_tokens': getattr(response.usage_metadata, 'prompt_token_count', 0),
                'completion_tokens': getattr(response.usage_metadata, 'candidates_token_count', 0),
                'total_tokens': getattr(response.usage_metadata, 'total_token_count', 0)
            }
        
        return ChatResponse(
            content=response.text,
            model=model,
            usage=usage,
            metadata={'system_instruction': system_inst, 'thinking_level': think_level}
        )
    
    async def stream_chat_response(
        self,
        messages: List[ChatMessage],
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        thinking_level: Optional[Literal["low", "high"]] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        if not messages:
            raise ValueError("Messages cannot be empty")
        
        system_inst, contents = self._convert_messages(messages)
        model = model_name or self.default_model_name
        temp = temperature if temperature is not None else self.default_temperature
        think_level = thinking_level if thinking_level is not None else self.default_thinking_level
        
        # Use official ThinkingLevel enum from google.genai.types
        # Low thinking: types.ThinkingLevel.LOW
        # High thinking: types.ThinkingLevel.HIGH
        thinking_level_enum = types.ThinkingLevel.LOW if think_level == "low" else types.ThinkingLevel.HIGH
        
        config_params = {
            'temperature': temp,
            'top_p': 0.95,
            'safety_settings': [
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
            ],
            'thinking_config': types.ThinkingConfig(thinking_level=thinking_level_enum),
            **kwargs
        }
        
        if max_tokens:
            config_params['max_output_tokens'] = max_tokens
        if system_inst:
            config_params['system_instruction'] = system_inst
        
        for chunk in self.client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(**config_params)
        ):
            if hasattr(chunk, 'text') and chunk.text:
                yield chunk.text
    
    def _clean_json_response(self, text: str) -> str:
        """Clean up JSON response from model output."""
        if not text:
            return "{}"
            
        # Remove markdown code blocks if present
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
            
        return text.strip()

    async def generate_chat_response_with_schema(
        self,
        messages: List[ChatMessage],
        response_schema: Dict[str, Any],
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        thinking_level: Optional[Literal["low", "high"]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        if not messages or not response_schema:
            raise ValueError("Messages and schema required")
        
        system_inst, contents = self._convert_messages(messages)
        model = model_name or self.default_model_name
        temp = temperature if temperature is not None else self.default_temperature
        think_level = thinking_level if thinking_level is not None else self.default_thinking_level
        
        # Use official ThinkingLevel enum from google.genai.types
        # Low thinking: types.ThinkingLevel.LOW
        # High thinking: types.ThinkingLevel.HIGH
        thinking_level_enum = types.ThinkingLevel.LOW if think_level == "low" else types.ThinkingLevel.HIGH
        
        config_params = {
            'temperature': temp,
            'top_p': 0.95,
            'safety_settings': [
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
            ],
            'thinking_config': types.ThinkingConfig(thinking_level=thinking_level_enum),
            'response_mime_type': 'application/json',
            'response_json_schema': response_schema,
            **kwargs
        }
        
        if system_inst:
            config_params['system_instruction'] = system_inst
        
        response = self.client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(**config_params)
        )
        
        # With response_json_schema, the model should return valid JSON
        # But we still clean it just in case, as thinking models can sometimes be verbose
        text = self._clean_json_response(response.text)
            
        return json.loads(text)
    
    async def count_tokens(self, messages: List[ChatMessage], model_name: Optional[str] = None, **kwargs) -> int:
        if not messages:
            raise ValueError("Messages cannot be empty")
        text = "\n".join([f"{m.role}: {m.content}" for m in messages])
        return len(text) // 4  # Rough estimate
