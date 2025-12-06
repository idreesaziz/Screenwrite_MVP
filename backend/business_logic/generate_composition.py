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


def fix_image_aspect_ratios(tracks: List[Dict]) -> List[Dict]:
    """
    Fix image/video aspect ratios by adding height:auto or width:auto when one dimension is set.
    
    When width or height is specified (as percentage or fixed value) on Img/Video elements,
    the other dimension should be 'auto' to preserve aspect ratio. This function adds the
    missing auto property to prevent distortion.
    
    Algorithm:
    - For each track → clips → elements
    - Parse element strings (format: "Tag;prop:value;...")
    - If element is Img or Video:
      - If width is set but height is not → add height:auto
      - If height is set but width is not → add width:auto
      - If both set or neither set → no change needed
    
    Args:
        tracks: List of track dictionaries with 'clips' arrays
        
    Returns:
        Modified tracks with aspect ratio fixes applied
    """
    fix_count = 0
    
    for track_idx, track in enumerate(tracks):
        clips = track.get('clips', [])
        
        for clip_idx, clip in enumerate(clips):
            element = clip.get('element', {})
            elements = element.get('elements', [])
            
            fixed_elements = []
            for elem_str in elements:
                # Parse element string: "Tag;prop1:value1;prop2:value2;..."
                if not elem_str or ';' not in elem_str:
                    fixed_elements.append(elem_str)
                    continue
                
                parts = elem_str.split(';')
                tag = parts[0]
                
                # Only fix Img and Video elements
                if tag not in ['Img', 'Video']:
                    fixed_elements.append(elem_str)
                    continue
                
                # Parse properties into dict
                props = {}
                for part in parts[1:]:
                    if ':' in part:
                        key, value = part.split(':', 1)
                        props[key] = value
                
                # Check if width/height need auto complement
                has_width = 'width' in props
                has_height = 'height' in props
                
                needs_fix = False
                if has_width and not has_height:
                    props['height'] = 'auto'
                    needs_fix = True
                    fix_count += 1
                    logger.info(
                        f"🔧 Fixed aspect ratio: Added height:auto to {tag} "
                        f"(track {track_idx}, clip '{clip.get('id')}')"
                    )
                elif has_height and not has_width:
                    props['width'] = 'auto'
                    needs_fix = True
                    fix_count += 1
                    logger.info(
                        f"🔧 Fixed aspect ratio: Added width:auto to {tag} "
                        f"(track {track_idx}, clip '{clip.get('id')}')"
                    )
                
                # Reconstruct element string
                if needs_fix:
                    reconstructed = tag
                    for key, value in props.items():
                        reconstructed += f';{key}:{value}'
                    fixed_elements.append(reconstructed)
                else:
                    fixed_elements.append(elem_str)
            
            # Update elements if any were fixed
            if element.get('elements') != fixed_elements:
                element['elements'] = fixed_elements
    
    if fix_count > 0:
        logger.info(f"✅ Fixed {fix_count} image/video aspect ratio(s) across all tracks")
    
    return tracks


def resolve_track_overlaps(tracks: List[Dict]) -> List[Dict]:
    """
    Resolve overlapping clips on the same track by shifting clips to the right.
    
    Algorithm:
    - For each track, sort clips by startTimeInSeconds
    - For each consecutive pair of clips (clip[i], clip[i+1]):
      - If clip[i].endTimeInSeconds > clip[i+1].startTimeInSeconds (overlap detected):
        - Calculate shift_amount = clip[i].endTimeInSeconds - clip[i+1].startTimeInSeconds
        - Add shift_amount to startTimeInSeconds and endTimeInSeconds of clip[i+1] and ALL subsequent clips
    
    Args:
        tracks: List of track dictionaries with 'clips' arrays
        
    Returns:
        Modified tracks with overlaps resolved
    """
    overlap_count = 0
    
    for track_idx, track in enumerate(tracks):
        clips = track.get('clips', [])
        
        if len(clips) <= 1:
            continue  # No overlaps possible with 0 or 1 clip
        
        # Sort clips by start time to ensure correct ordering
        clips.sort(key=lambda c: c.get('startTimeInSeconds', 0))
        
        # Check for overlaps and resolve them
        i = 0
        while i < len(clips) - 1:
            current_clip = clips[i]
            next_clip = clips[i + 1]
            
            current_end = current_clip.get('endTimeInSeconds', 0)
            next_start = next_clip.get('startTimeInSeconds', 0)
            
            # Check for overlap
            if current_end > next_start:
                overlap_count += 1
                shift_amount = current_end - next_start
                
                logger.warning(
                    f"⚠️ Overlap detected on track {track_idx}: "
                    f"clip '{current_clip.get('id')}' (ends at {current_end}s) overlaps with "
                    f"clip '{next_clip.get('id')}' (starts at {next_start}s). "
                    f"Shifting by {shift_amount}s"
                )
                
                # Shift the next clip and all subsequent clips
                for j in range(i + 1, len(clips)):
                    clips[j]['startTimeInSeconds'] = clips[j].get('startTimeInSeconds', 0) + shift_amount
                    clips[j]['endTimeInSeconds'] = clips[j].get('endTimeInSeconds', 0) + shift_amount
                    
                    logger.info(
                        f"  ↪️ Shifted clip '{clips[j].get('id')}' to "
                        f"{clips[j]['startTimeInSeconds']}s - {clips[j]['endTimeInSeconds']}s"
                    )
                
                # Don't increment i - check the same pair again in case the shift created new overlaps
                # (Though with proper shifting, this shouldn't happen, but being safe)
            else:
                i += 1
        
        # Update track with sorted and fixed clips
        track['clips'] = clips
    
    if overlap_count > 0:
        logger.info(f"✅ Resolved {overlap_count} overlap(s) across all tracks")
    
    return tracks


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
        safe_model_name = model_name
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
                model_name=safe_model_name
            )
            
            # Handle both formats: {"tracks": [...]} or just [...]
            # Some models wrap the array in a "tracks" object despite schema
            if isinstance(result_dict, dict) and "tracks" in result_dict:
                logger.info("Unwrapping 'tracks' wrapper from AI response")
                result_dict = result_dict["tracks"]
            
            # Safety check: Resolve any overlapping clips on the same track
            result_dict = resolve_track_overlaps(result_dict)
            
            # Safety check: Fix image/video aspect ratios
            result_dict = fix_image_aspect_ratios(result_dict)
            # Convert dict back to JSON string with proper formatting for diffs
            composition_json = json.dumps(result_dict, indent=2)
            
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
                    "model_name": safe_model_name or self.provider.default_model_name,
                    "temperature": temperature,
                    "media_library_count": len(media_library) if media_library else 0,
                    "had_current_composition": current_composition is not None,
                    "current_composition": current_composition,
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
                f"model={safe_model_name or 'default'}"
            )
            
            return CompositionGenerationResult(
                success=True,
                composition_code=composition_json,
                explanation=f"Generated composition for: {user_request}",
                duration=duration,
                model_used=safe_model_name or self.provider.default_model_name,
                metadata={"tracks_count": len(result_dict)}
            )
            
        except Exception as e:
            logger.error(f"❌ Composition generation failed: {str(e)}", exc_info=True)
            return CompositionGenerationResult(
                success=False,
                composition_code="[\n]",  # Empty composition fallback (formatted)
                explanation="Failed to generate composition",
                duration=5.0,
                model_used=safe_model_name or "unknown",
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
