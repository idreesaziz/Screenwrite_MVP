"""Google Gemini implem    def __init__(
        self,
        project_id: Optional[str] = None,
        location: str = "us-central1",
        default_model_name: str = "gemini-flash-latest",
        default_temperature: float = 1.0,
        default_thinking_budget: int = -1
    ): using Vertex AI."""

import json
import logging
import os
from typing import List, Dict, Any, AsyncIterator, Optional
from google import genai
from google.genai import types
from google.cloud import aiplatform

from services.base.ChatProvider import ChatProvider, ChatMessage, ChatResponse

logger = logging.getLogger(__name__)


class GeminiChatProvider(ChatProvider):
    """Gemini implementation using Vertex AI (Google Cloud Platform).
    
    Authentication is handled via Application Default Credentials (ADC):
    - Service account JSON file via GOOGLE_APPLICATION_CREDENTIALS env var
    - gcloud auth application-default login
    - Workload Identity (for GKE/Cloud Run)
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        location: str = "us-central1",
        default_model_name: str = "gemini-2.5-flash",
        default_temperature: float = 1.0,
        default_thinking_budget: Optional[int] = None
    ):
        """
        Initialize Vertex AI client using Application Default Credentials.
        
        Args:
            project_id: Google Cloud project ID (optional, will use from ADC if not provided)
            location: GCP region (default: us-central1)
            default_model_name: Default model to use
            default_temperature: Default temperature
            default_thinking_budget: Default thinking budget
        
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
        self.default_thinking_budget = default_thinking_budget
        
        # Initialize Vertex AI project and location
        aiplatform.init(project=self.project_id, location=self.location)
        
        # Initialize Vertex AI client using HttpOptions with api_version="v1beta"
        # This uses Application Default Credentials automatically
        self.client = genai.Client(
            http_options=types.HttpOptions(api_version="v1beta"),
        )
        logger.info(f"Initialized Vertex AI with model: {default_model_name}, project: {self.project_id}, location: {location}")
    
    def _convert_messages(self, messages: List[ChatMessage]):
        system_instruction = None
        contents = []
        
        for msg in messages:
            if msg.role == "system":
                system_instruction = msg.content if not system_instruction else system_instruction + "\n\n" + msg.content
            else:
                role = "model" if msg.role == "assistant" else "user"
                contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg.content)]))
        
        return system_instruction, contents
    
    async def generate_chat_response(
        self,
        messages: List[ChatMessage],
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        thinking_budget: Optional[int] = None,
        **kwargs
    ) -> ChatResponse:
        if not messages:
            raise ValueError("Messages cannot be empty")
        
        system_inst, contents = self._convert_messages(messages)
        model = model_name or self.default_model_name
        temp = temperature if temperature is not None else self.default_temperature
        think = thinking_budget if thinking_budget is not None else self.default_thinking_budget
        
        config_params = {
            'temperature': temp,
            'top_p': 0.95,
            'safety_settings': [
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
            ],
            'thinking_config': types.ThinkingConfig(thinking_budget=think),
            **kwargs
        }
        
        if max_tokens:
            config_params['max_output_tokens'] = max_tokens
        if system_inst:
            config_params['system_instruction'] = system_inst
        
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
            metadata={'system_instruction': system_inst}
        )
    
    async def stream_chat_response(
        self,
        messages: List[ChatMessage],
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        thinking_budget: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        if not messages:
            raise ValueError("Messages cannot be empty")
        
        system_inst, contents = self._convert_messages(messages)
        model = model_name or self.default_model_name
        temp = temperature if temperature is not None else self.default_temperature
        think = thinking_budget if thinking_budget is not None else self.default_thinking_budget
        
        config_params = {
            'temperature': temp,
            'top_p': 0.95,
            'safety_settings': [
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
            ],
            'thinking_config': types.ThinkingConfig(thinking_budget=think),
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
    
    async def generate_chat_response_with_schema(
        self,
        messages: List[ChatMessage],
        response_schema: Dict[str, Any],
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        thinking_budget: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        if not messages or not response_schema:
            raise ValueError("Messages and schema required")
        
        system_inst, contents = self._convert_messages(messages)
        model = model_name or self.default_model_name
        temp = temperature if temperature is not None else self.default_temperature
        think = thinking_budget if thinking_budget is not None else self.default_thinking_budget
        
        config_params = {
            'temperature': temp,
            'top_p': 0.95,
            'response_mime_type': 'application/json',
            'response_schema': response_schema,
            'safety_settings': [
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
            ],
            'thinking_config': types.ThinkingConfig(thinking_budget=think),
            **kwargs
        }
        
        if system_inst:
            config_params['system_instruction'] = system_inst
        
        response = self.client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(**config_params)
        )
        
        return json.loads(response.text)
    
    async def count_tokens(self, messages: List[ChatMessage], model_name: Optional[str] = None, **kwargs) -> int:
        if not messages:
            raise ValueError("Messages cannot be empty")
        text = "\n".join([f"{m.role}: {m.content}" for m in messages])
        return len(text) // 4  # Rough estimate
