"""
Business logic for composition generation using AI.

This service orchestrates the composition generation workflow:
1. Builds prompts with context (current composition, media library, history)
2. Calls AI provider with structured output schema
3. Parses and validates the response
4. Calculates composition metadata (duration, etc.)
5. Returns structured result
"""

import json
import logging
from dataclasses import dataclass
from typing import Optional, Dict, List, Any

from services.base.ChatProvider import ChatProvider, ChatMessage
from services.schemas.composition_schema import build_composition_schema
from prompts.composition_prompts import build_blueprint_prompt


logger = logging.getLogger(__name__)


@dataclass
class CompositionGenerationResult:
    """Result from composition generation"""
    success: bool
    composition_code: str  # JSON string of tracks array
    explanation: str
    duration: float
    model_used: str
    error_message: Optional[str] = None
    metadata: Optional[Dict] = None  # Token usage, thinking time, etc.


class CompositionGenerationService:
    """
    Service for generating video compositions using AI with structured output.
    
    Uses ChatProvider base class for swappable AI backends (Gemini, Claude, etc.)
    """
    
    def __init__(self, chat_provider: ChatProvider):
        """
        Initialize with chat provider for dependency injection.
        
        Args:
            chat_provider: AI chat provider (e.g., GeminiChatProvider)
        """
        self.provider = chat_provider
    
    async def generate_composition(
        self,
        user_request: str,
        preview_settings: Dict[str, Any],
        user_id: str,
        session_id: str,
        media_library: Optional[List[Dict]] = None,
        current_composition: Optional[List[Dict]] = None,
        preview_frame: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.1
    ) -> CompositionGenerationResult:
        """
        Generate or modify a video composition based on user request.
        
        Args:
            user_request: User's description of what they want
            preview_settings: Preview configuration (width, height, fps, etc.)
            user_id: User identifier for logging
            session_id: Session identifier for logging
            media_library: Available media files
            current_composition: Current tracks array for incremental editing
            preview_frame: Base64 screenshot of current frame
            model_name: Override default AI model
            temperature: Generation temperature (0.0-2.0)
        
        Returns:
            CompositionGenerationResult with generated composition or error
        """
        try:
            logger.info(
                f"Generating composition for user {user_id}, session {session_id}: {user_request[:100]}"
            )
            
            # Build request dict for prompt builder
            request_dict = {
                "user_request": user_request,
                "preview_settings": preview_settings,
                "media_library": media_library or [],
                "current_composition": current_composition
            }
            
            # Use the comprehensive prompt builder from old backend
            system_instruction, user_prompt = build_blueprint_prompt(request_dict)
            
            # Get composition schema for structured output
            composition_schema = build_composition_schema()
            
            # Build messages for chat provider
            messages = [
                ChatMessage(role="system", content=system_instruction),
                ChatMessage(role="user", content=user_prompt)
            ]
            
            # Generate with AI provider (structured output)
            result_dict = await self.provider.generate_chat_response_with_schema(
                messages=messages,
                response_schema=composition_schema,
                temperature=temperature,
                model_name=model_name
            )
            
            # Convert dict back to JSON string
            composition_json = json.dumps(result_dict)
            
            # Calculate duration from composition
            duration = self._calculate_duration(composition_json)
            
            # Save the edit request and generated code to logs
            try:
                from pathlib import Path
                from datetime import datetime
                
                logs_dir = Path(__file__).parent.parent / "logs"
                logs_dir.mkdir(exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                log_file = logs_dir / f"composition_edit_{session_id}_{timestamp}.json"
                
                edit_log = {
                    "timestamp": datetime.now().isoformat(),
                    "user_id": user_id,
                    "session_id": session_id,
                    "user_request": user_request,
                    "model_name": model_name or self.provider.default_model_name,
                    "temperature": temperature,
                    "media_library_count": len(media_library) if media_library else 0,
                    "had_current_composition": current_composition is not None,
                    "generated_code": composition_json,
                    "duration": duration,
                    "tracks_count": len(result_dict)
                }
                
                with open(log_file, "w") as f:
                    json.dump(edit_log, f, indent=2)
                
                logger.info(f"💾 Saved composition edit to: {log_file}")
            except Exception as log_error:
                logger.warning(f"Failed to save composition edit log: {log_error}")
            
            # Log successful generation
            logger.info(
                f"✅ Generated composition: {duration}s, "
                f"model={model_name or 'default'}"
            )
            
            return CompositionGenerationResult(
                success=True,
                composition_code=composition_json,
                explanation=f"Generated composition for: {user_request}",
                duration=duration,
                model_used=model_name or self.provider.default_model_name,
                metadata={"tracks_count": len(result_dict)}
            )
            
        except Exception as e:
            logger.error(f"❌ Composition generation failed: {str(e)}", exc_info=True)
            return CompositionGenerationResult(
                success=False,
                composition_code="[]",  # Empty composition fallback
                explanation="Failed to generate composition",
                duration=5.0,
                model_used=model_name or "unknown",
                error_message=str(e)
            )
    
    def _calculate_duration(self, composition_json: str) -> float:
        """Calculate total duration from composition JSON."""
        try:
            tracks = json.loads(composition_json)
            max_end_time = 0.0
            
            for track in tracks:
                for clip in track.get("clips", []):
                    end_time = clip.get("endTimeInSeconds", 0)
                    max_end_time = max(max_end_time, end_time)
            
            return max_end_time if max_end_time > 0 else 5.0
        except Exception as e:
            logger.warning(f"Failed to calculate duration: {e}")
            return 5.0  # Default fallback
