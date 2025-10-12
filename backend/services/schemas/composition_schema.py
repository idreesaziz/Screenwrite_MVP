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
    
    Example:
    "AbsoluteFill;id:root;parent:null;backgroundColor:#ff0000"
    "h1;id:title;parent:root;fontSize:48px;color:#fff;text:Hello World"
    """
    return {
        "type": "object",
        "properties": {
            "elements": {
                "type": "array",
                "items": {
                    "type": "string",
                    "description": "Element definition using DSL syntax: 'TagName;id:id;parent:parentId;prop:value;...'"
                },
                "description": "Array of element strings defining the visual structure"
            }
        },
        "required": ["elements"]
    }


def build_transition_schema() -> Dict[str, Any]:
    """
    Build schema for transition objects.
    
    Transitions create smooth visual effects between clips.
    Types: fade, slide, wipe, flip, clockWipe, iris
    """
    return {
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "enum": ["fade", "slide", "wipe", "flip", "clockWipe", "iris"],
                "description": "Type of transition effect"
            },
            "durationInSeconds": {
                "type": "number",
                "minimum": 0.1,
                "description": "Duration of the transition in seconds"
            },
            "direction": {
                "type": "string",
                "enum": ["left", "right", "up", "down"],
                "description": "Direction for directional transitions (slide, wipe)"
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
    
    Structure:
    [
      {
        "clips": [
          {
            "id": "clip-1",
            "startTimeInSeconds": 0,
            "endTimeInSeconds": 5,
            "element": {
              "elements": ["AbsoluteFill;id:root;parent:null;..."]
            },
            "transitionToNext": {...} (optional)
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
