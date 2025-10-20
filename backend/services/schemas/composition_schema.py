"""
Composition Blueprint JSON Schema for Structured Output

This schema defines the structure for video composition blueprints used by Remotion.
Each composition consists of tracks (layers) containing clips with timing and visual elements.
"""

from typing import Dict, Any


def build_element_schema() -> Dict[str, Any]:
    """
    Build schema for element objects with string-based element DSL.
    
    Element DSL format:
    "TagName;id:value;parent:value;property:value;..."
    
    IMPORTANT: The parser automatically prepends an implicit AbsoluteFill root element.
    - Root has id='root', name='AbsoluteFill', parentId=null
    - Use parent:root for top-level elements or omit parent field (defaults to root)
    - Do NOT create the root element yourself
    
    Example:
    "div;id:bg;parent:root;backgroundColor:#ff0000;width:100%;height:100%"
    "h1;id:title;fontSize:48px;color:#fff;text:Hello World"
    """
    return {
        "type": "object",
        "properties": {
            "elements": {
                "type": "array",
                "items": {
                    "type": "string",
                    "description": "Element definition using DSL syntax: 'TagName;id:id;parent:parentId;prop:value;...'. Parser adds implicit AbsoluteFill root - use parent:root for top-level."
                },
                "description": "Array of element strings. Parser automatically prepends AbsoluteFill root element."
            }
        },
        "required": ["elements"]
    }


def build_transition_schema() -> Dict[str, Any]:
    """
    Build schema for transition objects.
    
    Transitions create smooth visual effects between clips.
    Direction is encoded in the type name (e.g., slide-left, wipe-top-right).
    """
    return {
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "enum": [
                    # Basic transitions (no direction)
                    "fade",
                    "clock-wipe",
                    "iris",
                    # Slide transitions (4 directions)
                    "slide-left",
                    "slide-right",
                    "slide-top",
                    "slide-bottom",
                    # Wipe transitions (8 directions)
                    "wipe-left",
                    "wipe-right",
                    "wipe-top",
                    "wipe-bottom",
                    "wipe-top-left",
                    "wipe-top-right",
                    "wipe-bottom-left",
                    "wipe-bottom-right",
                    # Flip transitions (4 directions)
                    "flip-left",
                    "flip-right",
                    "flip-top",
                    "flip-bottom",
                    # Custom transitions
                    "zoom-in",
                    "zoom-out",
                    "blur",
                    "glitch"
                ],
                "description": "Type of transition effect (direction encoded in name)"
            },
            "durationInSeconds": {
                "type": "number",
                "minimum": 0.1,
                "description": "Duration of the transition in seconds"
            }
        },
        "required": ["type", "durationInSeconds"]
    }


def build_clip_schema() -> Dict[str, Any]:
    """
    Build schema for clip objects.
    
    Each clip represents a time segment with visual content.
    """
    return {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "description": "Unique identifier for the clip"
            },
            "startTimeInSeconds": {
                "type": "number",
                "minimum": 0,
                "description": "When the clip starts in the timeline (seconds)"
            },
            "endTimeInSeconds": {
                "type": "number",
                "minimum": 0,
                "description": "When the clip ends in the timeline (seconds)"
            },
            "element": build_element_schema(),
            "transitionFromPrevious": build_transition_schema(),
            "transitionToNext": build_transition_schema()
        },
        "required": ["id", "startTimeInSeconds", "endTimeInSeconds", "element"]
    }


def build_track_schema() -> Dict[str, Any]:
    """
    Build schema for track objects.
    
    Tracks are layers that stack on top of each other (like Photoshop layers).
    Track 0 = bottom layer, higher indices = layers on top.
    """
    return {
        "type": "object",
        "properties": {
            "clips": {
                "type": "array",
                "items": build_clip_schema(),
                "description": "Array of clips on this track/layer"
            }
        },
        "required": ["clips"]
    }


def build_composition_schema() -> Dict[str, Any]:
    """
    Build the complete composition blueprint schema.
    
    Returns a JSON schema for an array of tracks (layers).
    This is used for structured output with AI models.
    
    IMPORTANT: Parser automatically prepends AbsoluteFill root (id='root') to each clip.
    - Use parent:root for top-level elements or omit parent (defaults to root)
    - Do NOT create the root element yourself
    
    Structure:
    [
      {
        "clips": [
          {
            "id": "clip-1",
            "startTimeInSeconds": 0,
            "endTimeInSeconds": 5,
            "element": {
              "elements": [
                "div;id:bg;backgroundColor:#000;width:100%;height:100%",
                "h1;id:title;parent:bg;fontSize:64px;color:#fff;text:Hello"
              ]
            },
            "transitionToNext": {"type": "fade", "durationInSeconds": 1}
          }
        ]
      }
    ]
    """
    return {
        "type": "array",
        "items": build_track_schema(),
        "description": "Array of tracks/layers in the composition (index 0 = bottom layer)"
    }
