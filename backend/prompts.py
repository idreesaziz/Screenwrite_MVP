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
            "AbsoluteFill;id:root;parent:null;backgroundColor:#000;display:flex;justifyContent:center;alignItems:center",
            "h1;id:title;parent:root;fontSize:48px;color:#fff;fontWeight:700;text:Hello World"
          ]
        }
      }
    ]
  }
]

**ELEMENT FORMAT (CRITICAL)**

Each element is a semicolon-separated string in format:
ComponentName;id:uniqueId;parent:parentId;property:value;property:value;text:content

REQUIRED FIELDS:
- id: Unique identifier (must be unique across all elements)
- parent: Parent element id (use "null" for root element)

FORMAT RULES:
- Semicolons separate all properties
- Format: property:value
- Use camelCase for property names (fontSize not font-size)
- No quotes around values
- Text content: text:Your text here (can contain spaces)
- Arrays: colors:[#ff0000,#00ff00,#0000ff] (square brackets, no spaces between items)

COMPONENTS:
- AbsoluteFill: Full-screen container (use as root)
- Video, Audio, Img: Media elements (require src property with exact URL)
- div, span, h1, h2, h3, p: Text and container elements
- BlurText, TypewriterText, GradientText: Text animations

KEY PROPERTIES:
- Layout: display, position, top, left, right, bottom, width, height
- Flexbox: flexDirection, justifyContent, alignItems, gap
- Typography: fontSize, fontWeight, fontFamily, color, textAlign
- Styling: backgroundColor, background, opacity, transform, borderRadius
- Media: src (exact URL), volume, startFrom, endAt, muted
- Animation: text, delay, duration, direction, animateBy

EXAMPLES:
"AbsoluteFill;id:root;parent:null;backgroundColor:#000;display:flex;justifyContent:center;alignItems:center"
"Video;id:bg;parent:root;src:/exact-url.mp4;volume:0.5;width:100%;height:100%"
"h1;id:title;parent:root;fontSize:48px;color:#fff;fontWeight:700;text:Hello World"
"div;id:box;parent:root;background:linear-gradient(to right, #ff0000, #0000ff);padding:20px;borderRadius:8px"
"BlurText;id:blur1;parent:root;text:Fade In;fontSize:32px;delay:0.5;duration:1;direction:up;color:#fff"

**RULES**

1. Root element MUST have parent:null
2. All other elements MUST reference valid parent via parent:parentId
3. Use exact media URLs provided - never use generic filenames
4. Clips on same track cannot overlap in time
5. Complex CSS values work (rgba(255,0,0,0.5), translate(-50%, -50%), etc)
6. Always include id and parent fields for every element

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
