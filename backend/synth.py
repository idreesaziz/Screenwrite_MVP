
"""
Synth - Simplified Request Enhancement Engine

Two simple functions to enhance user requests:
1. enhance_without_media() - Basic textual enhancement
2. enhance_with_media() - Enhancement with media content analysis
"""

import json
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types


# Common system instruction shared by both enhancement functions
COMMON_SYSTEM_INSTRUCTION = """You are an AI Director for video composition. Your mission: transform vague user requests into super-specific, professionally polished execution plans.

⚠️ CORE RESPONSIBILITY: Fill missing details with precise specifications while ensuring professional visual quality.

⚠️ CRITICAL MEDIA RULE: NEVER hallucinate or invent media files. ONLY use media files that are explicitly provided in the available media library. If no media files are available, create compositions using text, shapes, animations, and visual effects only - NO video, image, or audio file references.

⚠️ CRITICAL MEDIA FILE NAMING: Always use exact file names from the available media library. Never use generic names like "video.mp4" or "image.jpg".

⚠️ SUPER-SPECIFIC REFERENCING: When referring to any element, be extremely precise:
- Exact file names (xyz.mp4, not "video") - ONLY if they exist in the media library
- Specific measurements (48px font size, not "large text")
- Precise positioning (upper-right intersection using golden ratio, not "top corner")
- Exact timing (0.5s fade-in duration, not "quick transition")
- Specific colors (rgba(255,255,255,0.9), not "white-ish")

TRANSFORMATION EXAMPLES:

USER: "Add text saying 'Hello'"
AI DIRECTOR: 
TYPOGRAPHY SPECIFICATION:
- Display "Hello" using Inter font, 48px size, 600 font weight
- Position at center-top (50%% horizontal, 15%% vertical from top)
- Color: white (#FFFFFF) with 1px black text-shadow for contrast
- Animation: fade-in over 0.5s with ease-out timing

USER: "Add my logo"  
AI DIRECTOR:
BRAND INTEGRATION:
- Position logo at golden ratio intersection (61.8%% from left, 38.2%% from top)
- Scale to 8%% of viewport width, maintain aspect ratio
- Add drop shadow: 2px offset, rgba(0,0,0,0.1) color, 4px blur
- Breathing animation: 0.8s duration, 98%%-102%% scale variation, infinite loop

USER: "Add the shore video"
AI DIRECTOR: "Add shore.mp4 with full viewport coverage (100%% width/height), object-fit: cover, fade-in transition over 0.8s duration starting at 0 seconds"

SPECIFICATION STANDARDS:
- Typography: Exact font family, size in px, weight, line-height
- Colors: Hex codes or rgba values with specific opacity
- Positioning: Precise percentages or pixel values
- Animations: Exact duration, easing functions, keyframe specifications
- Timing: Start/end times in seconds with decimal precision

Return ONLY the detailed execution plan - no explanations or questions."""


async def synthesize_request(
    user_request: str,
    conversation_history: Optional[List[Dict[str, Any]]],
    current_composition: Optional[str],
    relevant_media_files: List[str],
    media_library: Optional[List[Dict[str, Any]]],
    preview_settings: Dict[str, Any],
    gemini_api: Any
) -> str:
    """
    Enhanced Synth: Route to appropriate enhancement function based on media availability
    """
    
    print(f"🧠 Synth: Processing request with {len(relevant_media_files)} relevant media files")
    
    if not relevant_media_files:
        # No media analysis needed - use basic enhancement
        return await enhance_without_media(
            user_request, conversation_history, current_composition, 
            media_library, preview_settings, gemini_api
        )
    else:
        # Media analysis needed - use enhanced enhancement
        return await enhance_with_media(
            user_request, conversation_history, current_composition,
            relevant_media_files, media_library, gemini_api
        )


async def enhance_without_media(
    user_request: str,
    conversation_history: Optional[List[Dict[str, Any]]],
    current_composition: Optional[str],
    media_library: Optional[List[Dict[str, Any]]],
    preview_settings: Dict[str, Any],
    gemini_api: Any
) -> str:
    """Simple enhancement without media analysis - resolve textual ambiguities only"""
    
    print("🧠 Synth: Enhancing without media analysis")
    
    # Build simple context
    context_parts = [f"User request: {user_request}"]
    
    if conversation_history:
        recent = conversation_history[-4:]  # Last 2 exchanges
        context_parts.append("Recent conversation:")
        for msg in recent:
            # Handle ConversationMessage Pydantic model
            if hasattr(msg, 'user_request') and hasattr(msg, 'ai_response'):
                context_parts.append(f"user: {msg.user_request}")
                context_parts.append(f"assistant: {msg.ai_response}")
            else:
                # Fallback for dict format
                role = msg.get('role', 'unknown') if hasattr(msg, 'get') else getattr(msg, 'role', 'unknown')
                content = msg.get('content', '') if hasattr(msg, 'get') else getattr(msg, 'content', '')
                context_parts.append(f"{role}: {content}")
    
    if current_composition:
        context_parts.append(f"Current composition exists (duration context available)")
    
    # Add available media files for filename reference
    if media_library:
        context_parts.append("Available media files:")
        for media_item in media_library:
            media_name = media_item.get('name', 'unknown')
            media_type = media_item.get('mediaType', 'unknown')
            context_parts.append(f"- {media_name} ({media_type})")
    
    context_text = "\n".join(context_parts)

    # Use common system instruction
    system_instruction = COMMON_SYSTEM_INSTRUCTION

    # User prompt with context
    prompt = f"""USER REQUEST: "{user_request}"

CONTEXT:
- Current Composition Code: {current_composition or "No current composition"}
- Conversation History: {context_text}"""

    try:
        response = gemini_api.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=1.0
            )
        )
        
        if response and response.text:
            enhanced = response.text.strip()
            print(f"✅ Synth: Enhanced without media: '{enhanced[:100]}...'\n")
            return enhanced
        else:
            return f"Apply the following change: {user_request}"
            
    except Exception as e:
        print(f"❌ Synth: Enhancement failed: {e}")
        return f"Apply the following change: {user_request}"


async def enhance_with_media(
    user_request: str,
    conversation_history: Optional[List[Dict[str, Any]]],
    current_composition: Optional[str],
    relevant_media_files: List[str],
    media_library: Optional[List[Dict[str, Any]]],
    gemini_api: Any
) -> str:
    """Enhanced enhancement with media content analysis"""
    
    print(f"🧠 Synth: Enhancing with {len(relevant_media_files)} media files")
    
    # Build context with media info
    context_parts = [f"User request: {user_request}"]
    
    if conversation_history:
        recent = conversation_history[-4:]
        context_parts.append("Recent conversation:")
        for msg in recent:
            # Handle ConversationMessage Pydantic model
            if hasattr(msg, 'user_request') and hasattr(msg, 'ai_response'):
                context_parts.append(f"user: {msg.user_request}")
                context_parts.append(f"assistant: {msg.ai_response}")
            else:
                # Fallback for dict format
                role = msg.get('role', 'unknown') if hasattr(msg, 'get') else getattr(msg, 'role', 'unknown')
                content = msg.get('content', '') if hasattr(msg, 'get') else getattr(msg, 'content', '')
                context_parts.append(f"{role}: {content}")
    
    # Extract composition duration for timing calculations
    duration = 0.0
    if current_composition:
        import re
        duration_patterns = [
            r'DURATION:\s*(\d+(?:\.\d+)?)',
            r'AI-determined Duration:\s*(\d+(?:\.\d+)?)\s*seconds'
        ]
        for pattern in duration_patterns:
            match = re.search(pattern, current_composition)
            if match:
                duration = float(match.group(1))
                break
        context_parts.append(f"Current composition duration: {duration} seconds")
    
    # Add media file info
    context_parts.append("Relevant media files:")
    for media_name in relevant_media_files:
        if media_library:
            media_item = next((m for m in media_library if m.get('name') == media_name), None)
            if media_item:
                media_type = media_item.get('mediaType', 'unknown')
                media_duration = media_item.get('durationInSeconds', 0)
                if media_type == 'video' and media_duration:
                    context_parts.append(f"- {media_name}: {media_type} ({media_duration}s)")
                else:
                    context_parts.append(f"- {media_name}: {media_type}")
    
    context_text = "\n".join(context_parts)
    
    # System instruction with role, requirements and examples
    system_instruction = COMMON_SYSTEM_INSTRUCTION + """

CRITICAL: SOURCE MEDIA TIMING REFERENCE
When analyzing video content and referencing specific moments, always specify timestamps as they appear in the SOURCE MEDIA FILE with clear file identification.

⚠️ TIMING INSTRUCTION: Reference video moments using their original timestamps from the source media file. Always clearly specify which media file the timestamp refers to. The code generator will handle composition timing conversion.

⚠️ KEY PATTERNS FOR VIDEO REFERENCE:
- Timing: "at X seconds in source media file 'filename.ext'"

⚠️ FOCUS ON CREATIVE INTENT: Do not output technical implementation. Focus purely on creative direction and visual specifications.

Return ONLY the creative execution plan - no code, no explanations, no questions."""

    # User prompt with specific request and context
    prompt = f"""USER REQUEST: "{user_request}"

CONTEXT:
- Current Composition Code: {current_composition or "No current composition"}
- Conversation History: {context_text}
- Relevant Media Files: {len(relevant_media_files)} files for analysis"""

    try:
        # Prepare content for Gemini (text + media files)
        content_parts = [prompt]
        
        # Add media files with Gemini file IDs
        if media_library:
            for media_name in relevant_media_files:
                media_item = next((m for m in media_library if m.get('name') == media_name), None)
                if media_item and media_item.get('gemini_file_id'):
                    try:
                        gemini_file = gemini_api.files.get(name=media_item['gemini_file_id'])
                        content_parts.append(gemini_file)
                        print(f"🧠 Synth: Added {media_name} for analysis")
                    except Exception as e:
                        print(f"⚠️ Synth: Failed to load {media_name}: {e}")
        
        response = gemini_api.models.generate_content(
            model="gemini-2.5-flash",
            contents=content_parts,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=1.0
            )
        )
        
        if response and response.text:
            enhanced = response.text.strip()
            print(f"✅ Synth: Enhanced with media: '{enhanced}...'\n")
            return enhanced
        else:
            return f"Apply the following change: {user_request} (using relevant media files)"
            
    except Exception as e:
        print(f"❌ Synth: Media enhancement failed: {e}")
        return f"Apply the following change: {user_request} (using relevant media files)"
