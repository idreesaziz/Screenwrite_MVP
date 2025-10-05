"""
Element Object Schema Module

Flat element list structure with parent references - avoids recursion complexity.
Each element has an ID and optional parentId to build the tree structure.
"""

def build_simple_element_schema():
    """
    Flat element list schema - no recursion, just parent references.
    
    Structure:
    {
      "elements": [
        {"id": "root", "name": "AbsoluteFill", "parentId": null, "props": {...}},
        {"id": "div1", "name": "div", "parentId": "root", "props": {...}},
        {"id": "span1", "name": "span", "parentId": "div1", "props": {...}, "text": "Hello"}
      ]
    }
    
    This avoids recursive schema validation while maintaining full nesting capability.
    """
    return {
        "type": "object",
        "properties": {
            "elements": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string",
                            "description": "Unique identifier for this element"
                        },
                        "name": {
                            "type": "string",
                            "enum": [
                                # Media components
                                "Video", "Audio", "Img",
                                # Container
                                "AbsoluteFill",
                                # HTML elements
                                "div", "span", "h1", "h2", "h3", "p"
                            ],
                            "description": "Element type name"
                        },
                        "parentId": {
                            "type": "string",
                            "description": "ID of parent element. Null for root element."
                        },
                        "props": {
                            "type": "object",
                            "properties": {
                                "style": {
                                    "type": "object",
                                    "properties": {
                                        "width": {"type": "string"},
                                        "height": {"type": "string"},
                                        "backgroundColor": {"type": "string"},
                                        "background": {"type": "string"},
                                        "color": {"type": "string"},
                                        "fontSize": {"type": "string"},
                                        "fontWeight": {"type": "string"},
                                        "fontFamily": {"type": "string"},
                                        "textAlign": {"type": "string"},
                                        "textShadow": {"type": "string"},
                                        "display": {"type": "string"},
                                        "justifyContent": {"type": "string"},
                                        "alignItems": {"type": "string"},
                                        "position": {"type": "string"},
                                        "top": {"type": "string"},
                                        "left": {"type": "string"},
                                        "transform": {"type": "string"},
                                        "opacity": {"type": "string"}
                                    }
                                },
                                "src": {"type": "string"},
                                "volume": {"type": "number"},
                                "startFrom": {"type": "number"},
                                "endAt": {"type": "number"}
                            },
                            "description": "Element properties: style object for CSS, media properties for Video/Audio/Img"
                        },
                        "text": {
                            "type": "string",
                            "description": "Text content for this element (if any)"
                        }
                    },
                    "required": ["id", "name"]
                },
                "description": "Flat list of all elements in the composition tree"
            }
        },
        "required": ["elements"]
    }
