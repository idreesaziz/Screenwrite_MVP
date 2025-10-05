# System instructions and prompt templates for blueprint generation

SYSTEM_INSTRUCTION = """
You are a video composition generator. Create JSON for a multi-track video timeline.

**STRUCTURE**

Return a JSON array of tracks. Each track contains clips with timing and elements:

[
  {
    "clips": [
      {
        "id": "unique-id",
        "startTimeInSeconds": 0,
        "endTimeInSeconds": 5,
        "element": {
          "elements": [
            {"id": "root", "name": "AbsoluteFill", "parentId": null, "props": {"style": {"backgroundColor": "#000"}}},
            {"id": "text1", "name": "span", "parentId": "root", "props": {"style": {"color": "#fff", "fontSize": "48px"}}, "text": "Hello"}
          ]
        }
      }
    ]
  }
]

**ELEMENT STRUCTURE (CRITICAL)**

Each element in the "elements" array must have:
- id: unique identifier (required)
- name: component type - "AbsoluteFill", "Video", "Audio", "Img", "div", "span", "h1", "p" (required)
- parentId: ID of parent element, or null for root (required)
- props: object with properties (optional)
  - style: object with CSS properties like {backgroundColor: "#000", fontSize: "48px"}
  - src: URL for Video/Audio/Img components  
  - volume, startFrom, endAt: for media components
- text: text content for this element (optional)

DO NOT use nested "children" arrays. Build tree using parentId references.

**RULES**

1. Root element must have "parentId": null
2. Other elements reference parent via "parentId"
3. Use "text" field for text content, not children
4. CSS properties go in props.style object, in camelCase (backgroundColor not background-color)
5. Clips on same track cannot overlap in time
6. Use exact media URLs provided, never generic filenames

Return valid JSON matching the structure above.
"""


def build_system_instruction() -> str:
    """Build the complete system instruction for blueprint generation"""
    return SYSTEM_INSTRUCTION


def build_media_section(media_library: list) -> str:
    """Build media assets section for the prompt"""
    if not media_library or len(media_library) == 0:
        return "\nNo media assets available. Create compositions using text, shapes, and animations only.\n"
    
    media_section = "\nAVAILABLE MEDIA ASSETS:\n"
    for media in media_library:
        name = media.get('name', 'unnamed')
        media_type = media.get('mediaType', 'unknown')
        duration = media.get('durationInSeconds', 0)
        media_width = media.get('media_width', 0)
        media_height = media.get('media_height', 0)
        media_url_local = media.get('mediaUrlLocal', '')
        media_url_remote = media.get('mediaUrlRemote', '')
        
        actual_url = media_url_remote if media_url_remote else media_url_local
        
        if media_type == 'video':
            media_info = f"- {name}: Video"
            if media_width and media_height:
                media_info += f" ({media_width}x{media_height})"
            if duration:
                media_info += f" ({duration}s)"
            media_info += f" - URL: {actual_url}\n"
            media_section += media_info
        elif media_type == 'image':
            media_info = f"- {name}: Image"
            if media_width and media_height:
                media_info += f" ({media_width}x{media_height})"
            media_info += f" - URL: {actual_url}\n"
            media_section += media_info
        elif media_type == 'audio':
            media_info = f"- {name}: Audio"
            if duration:
                media_info += f" ({duration}s)"
            media_info += f" - URL: {actual_url}\n"
            media_section += media_info
    
    media_section += "\nUSE THE EXACT URLS PROVIDED ABOVE.\n"
    
    return media_section


def build_composition_context(current_composition: list) -> str:
    """Build context section for incremental editing"""
    if not current_composition or len(current_composition) == 0:
        return ""
    
    composition_context = f"\nEXISTING COMPOSITION: {len(current_composition)} tracks, "
    clip_count = sum(len(track.get('clips', [])) for track in current_composition)
    composition_context += f"{clip_count} clips total.\n"
    composition_context += f"Add to or modify this composition based on the user request.\n"
    
    return composition_context


def build_blueprint_prompt(request: dict) -> tuple[str, str]:
    """Build system instruction and user prompt for blueprint generation"""
    system_instruction = build_system_instruction()
    
    media_section = build_media_section(request.get('media_library', []))
    composition_context = build_composition_context(request.get('current_composition', []))
    
    user_prompt = f"""USER REQUEST: {request.get('user_request', '')}
{composition_context}
{media_section}"""

    return system_instruction, user_prompt
