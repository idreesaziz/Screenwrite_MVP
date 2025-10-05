"""
Comprehensive Element Object Schema for Vertex AI Structured Output

This module defines detailed schemas for all component types with element-specific
prop validation. Uses Vertex AI's anyOf feature to enforce element-specific requirements.
"""

def get_common_css_props():
    """
    Returns comprehensive CSS properties that can be used by any element.
    Covers layout, positioning, styling, transforms, and animations.
    """
    return {
        # Layout & Box Model
        "display": {"type": "string"},
        "position": {"type": "string"},
        "top": {"type": "string"},
        "right": {"type": "string"},
        "bottom": {"type": "string"},
        "left": {"type": "string"},
        "width": {"type": "string"},
        "height": {"type": "string"},
        "minWidth": {"type": "string"},
        "maxWidth": {"type": "string"},
        "minHeight": {"type": "string"},
        "maxHeight": {"type": "string"},
        "margin": {"type": "string"},
        "marginTop": {"type": "string"},
        "marginRight": {"type": "string"},
        "marginBottom": {"type": "string"},
        "marginLeft": {"type": "string"},
        "padding": {"type": "string"},
        "paddingTop": {"type": "string"},
        "paddingRight": {"type": "string"},
        "paddingBottom": {"type": "string"},
        "paddingLeft": {"type": "string"},
        
        # Flexbox
        "flex": {"type": "string"},
        "flexDirection": {"type": "string"},
        "flexWrap": {"type": "string"},
        "flexGrow": {"type": "number"},
        "flexShrink": {"type": "number"},
        "flexBasis": {"type": "string"},
        "justifyContent": {"type": "string"},
        "alignItems": {"type": "string"},
        "alignSelf": {"type": "string"},
        "alignContent": {"type": "string"},
        "gap": {"type": "string"},
        "rowGap": {"type": "string"},
        "columnGap": {"type": "string"},
        
        # Grid
        "gridTemplateColumns": {"type": "string"},
        "gridTemplateRows": {"type": "string"},
        "gridTemplateAreas": {"type": "string"},
        "gridColumn": {"type": "string"},
        "gridRow": {"type": "string"},
        "gridArea": {"type": "string"},
        "gridAutoFlow": {"type": "string"},
        "gridAutoColumns": {"type": "string"},
        "gridAutoRows": {"type": "string"},
        
        # Typography
        "color": {"type": "string"},
        "fontSize": {"type": "string"},
        "fontFamily": {"type": "string"},
        "fontWeight": {"type": "string"},
        "fontStyle": {"type": "string"},
        "lineHeight": {"type": "string"},
        "letterSpacing": {"type": "string"},
        "textAlign": {"type": "string"},
        "textDecoration": {"type": "string"},
        "textTransform": {"type": "string"},
        "textShadow": {"type": "string"},
        "whiteSpace": {"type": "string"},
        "wordBreak": {"type": "string"},
        "wordWrap": {"type": "string"},
        "textOverflow": {"type": "string"},
        
        # Background
        "background": {"type": "string"},
        "backgroundColor": {"type": "string"},
        "backgroundImage": {"type": "string"},
        "backgroundSize": {"type": "string"},
        "backgroundPosition": {"type": "string"},
        "backgroundRepeat": {"type": "string"},
        "backgroundAttachment": {"type": "string"},
        "backgroundClip": {"type": "string"},
        "backgroundOrigin": {"type": "string"},
        
        # Border
        "border": {"type": "string"},
        "borderWidth": {"type": "string"},
        "borderStyle": {"type": "string"},
        "borderColor": {"type": "string"},
        "borderTop": {"type": "string"},
        "borderRight": {"type": "string"},
        "borderBottom": {"type": "string"},
        "borderLeft": {"type": "string"},
        "borderRadius": {"type": "string"},
        "borderTopLeftRadius": {"type": "string"},
        "borderTopRightRadius": {"type": "string"},
        "borderBottomLeftRadius": {"type": "string"},
        "borderBottomRightRadius": {"type": "string"},
        
        # Visual Effects
        "opacity": {"type": "number"},
        "visibility": {"type": "string"},
        "overflow": {"type": "string"},
        "overflowX": {"type": "string"},
        "overflowY": {"type": "string"},
        "zIndex": {"type": "number"},
        "boxShadow": {"type": "string"},
        "filter": {"type": "string"},
        "backdropFilter": {"type": "string"},
        "mixBlendMode": {"type": "string"},
        "isolation": {"type": "string"},
        
        # Transform & Animation
        "transform": {"type": "string"},
        "transformOrigin": {"type": "string"},
        "transformStyle": {"type": "string"},
        "perspective": {"type": "string"},
        "perspectiveOrigin": {"type": "string"},
        "backfaceVisibility": {"type": "string"},
        
        # Transitions (values, not used for animation in our system)
        "transition": {"type": "string"},
        "transitionProperty": {"type": "string"},
        "transitionDuration": {"type": "string"},
        "transitionTimingFunction": {"type": "string"},
        "transitionDelay": {"type": "string"},
        
        # Animation (values, not used for animation in our system)
        "animation": {"type": "string"},
        "animationName": {"type": "string"},
        "animationDuration": {"type": "string"},
        "animationTimingFunction": {"type": "string"},
        "animationDelay": {"type": "string"},
        "animationIterationCount": {"type": "string"},
        "animationDirection": {"type": "string"},
        "animationFillMode": {"type": "string"},
        "animationPlayState": {"type": "string"},
        
        # Cursor & Interaction
        "cursor": {"type": "string"},
        "pointerEvents": {"type": "string"},
        "userSelect": {"type": "string"},
        
        # Other
        "objectFit": {"type": "string"},
        "objectPosition": {"type": "string"},
        "listStyle": {"type": "string"},
        "listStyleType": {"type": "string"},
        "listStylePosition": {"type": "string"},
        "listStyleImage": {"type": "string"},
        "verticalAlign": {"type": "string"},
        "clipPath": {"type": "string"},
        "mask": {"type": "string"},
        "willChange": {"type": "string"},
        "content": {"type": "string"},
    }


def get_video_element_schema(children_schema):
    """Schema for Video component - plays video files"""
    props = {
        # Video-specific props
        "src": {"type": "string"},  # Required - video file URL
        "startFrom": {"type": "number"},  # Optional - start frame
        "endAt": {"type": "number"},  # Optional - end frame
        "volume": {"type": "number"},  # Optional - 0.0 to 1.0
    }
    # Add all CSS props
    props.update(get_common_css_props())
    
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string", "enum": ["Video"]},
            "props": {
                "type": "object",
                "properties": props,
                "required": ["src"]  # src is required for Video
            },
            "children": children_schema
        },
        "required": ["name"]
    }


def get_audio_element_schema(children_schema):
    """Schema for Audio component - plays audio files"""
    props = {
        # Audio-specific props
        "src": {"type": "string"},  # Required - audio file URL
        "startFrom": {"type": "number"},  # Optional - start frame
        "endAt": {"type": "number"},  # Optional - end frame
        "volume": {"type": "number"},  # Optional - 0.0 to 1.0
    }
    # Audio doesn't need CSS props (it's not visual)
    
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string", "enum": ["Audio"]},
            "props": {
                "type": "object",
                "properties": props,
                "required": ["src"]  # src is required for Audio
            },
            "children": children_schema
        },
        "required": ["name"]
    }


def get_img_element_schema(children_schema):
    """Schema for Img component - displays static images"""
    props = {
        # Img-specific props
        "src": {"type": "string"},  # Required - image file URL
    }
    # Add all CSS props
    props.update(get_common_css_props())
    
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string", "enum": ["Img"]},
            "props": {
                "type": "object",
                "properties": props,
                "required": ["src"]  # src is required for Img
            },
            "children": children_schema
        },
        "required": ["name"]
    }


def get_absolute_fill_element_schema(children_schema):
    """Schema for AbsoluteFill component - full-screen container"""
    props = get_common_css_props()
    
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string", "enum": ["AbsoluteFill"]},
            "props": {
                "type": "object",
                "properties": props
                # No required props
            },
            "children": children_schema
        },
        "required": ["name"]
    }


def get_html_element_schema(element_name, children_schema):
    """Schema for standard HTML elements (div, span, h1, etc.)"""
    props = get_common_css_props()
    
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string", "enum": [element_name]},
            "props": {
                "type": "object",
                "properties": props
                # No required props
            },
            "children": children_schema
        },
        "required": ["name"]
    }


def get_split_text_element_schema(children_schema):
    """Schema for SplitText component - animates text by splitting characters/words"""
    props = {
        "text": {"type": "string"},
        "animateBy": {"type": "string"},
        "direction": {"type": "string"},
        "delay": {"type": "number"},
        "duration": {"type": "number"}
    }
    props.update(get_common_css_props())
    
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string", "enum": ["SplitText"]},
            "props": {
                "type": "object",
                "properties": props
            },
            "children": children_schema
        },
        "required": ["name"]
    }


def get_blur_text_element_schema(children_schema):
    """Schema for BlurText component - animates text with blur effects"""
    props = {
        "text": {"type": "string"},
        "animateBy": {"type": "string"},
        "direction": {"type": "string"},
        "delay": {"type": "number"},
        "duration": {"type": "number"}
    }
    props.update(get_common_css_props())
    
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string", "enum": ["BlurText"]},
            "props": {
                "type": "object",
                "properties": props
            },
            "children": children_schema
        },
        "required": ["name"]
    }


def get_typewriter_text_element_schema(children_schema):
    """Schema for TypewriterText component - typewriter animation with cursor"""
    props = {
        "text": {"type": "string"},
        "typingSpeed": {"type": "number"},
        "initialDelay": {"type": "number"},
        "pauseDuration": {"type": "number"},
        "deletingSpeed": {"type": "number"},
        "loop": {"type": "boolean"},
        "showCursor": {"type": "boolean"},
        "cursorCharacter": {"type": "string"},
        "cursorBlinkSpeed": {"type": "number"}
    }
    props.update(get_common_css_props())
    
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string", "enum": ["TypewriterText"]},
            "props": {
                "type": "object",
                "properties": props
            },
            "children": children_schema
        },
        "required": ["name"]
    }


def get_shuffle_element_schema(children_schema):
    """Schema for Shuffle component - shuffles/scrambles text with color transitions"""
    props = {
        "text": {"type": "string"},
        "shuffleDirection": {"type": "string"},
        "duration": {"type": "number"},
        "delay": {"type": "number"},
        "stagger": {"type": "number"},
        "shuffleTimes": {"type": "number"},
        "animationMode": {"type": "string"},
        "scrambleCharset": {"type": "string"},
        "colorFrom": {"type": "string"},
        "colorTo": {"type": "string"}
    }
    props.update(get_common_css_props())
    
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string", "enum": ["Shuffle"]},
            "props": {
                "type": "object",
                "properties": props
            },
            "children": children_schema
        },
        "required": ["name"]
    }


def get_gradient_text_element_schema(children_schema):
    """Schema for GradientText component - animates gradient colors across text"""
    props = {
        "text": {"type": "string"},
        "colors": {"type": "array"},
        "animationSpeed": {"type": "number"},
        "showBorder": {"type": "boolean"}
    }
    props.update(get_common_css_props())
    
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string", "enum": ["GradientText"]},
            "props": {
                "type": "object",
                "properties": props
            },
            "children": children_schema
        },
        "required": ["name"]
    }


def get_decrypted_text_element_schema(children_schema):
    """Schema for DecryptedText component - decryption animation effect"""
    props = {
        "text": {"type": "string"},
        "speed": {"type": "number"},
        "sequential": {"type": "boolean"},
        "revealDirection": {"type": "string"},
        "useOriginalCharsOnly": {"type": "boolean"},
        "characters": {"type": "string"},
        "delay": {"type": "number"}
    }
    props.update(get_common_css_props())
    
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string", "enum": ["DecryptedText"]},
            "props": {
                "type": "object",
                "properties": props
            },
            "children": children_schema
        },
        "required": ["name"]
    }


def get_true_focus_element_schema(children_schema):
    """Schema for TrueFocus component - focus animation with blur, border, and glow"""
    props = {
        "text": {"type": "string"},
        "blurAmount": {"type": "number"},
        "borderColor": {"type": "string"},
        "glowColor": {"type": "string"},
        "animationDuration": {"type": "number"},
        "pauseBetweenAnimations": {"type": "number"},
        "delay": {"type": "number"}
    }
    props.update(get_common_css_props())
    
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string", "enum": ["TrueFocus"]},
            "props": {
                "type": "object",
                "properties": props
            },
            "children": children_schema
        },
        "required": ["name"]
    }


def get_glitch_text_element_schema(children_schema):
    """Schema for GlitchText component - glitch effect with shadows and intensity control"""
    props = {
        "text": {"type": "string"},
        "speed": {"type": "number"},
        "enableShadows": {"type": "boolean"},
        "shadowColors": {"type": "array"},
        "glitchIntensity": {"type": "number"},
        "delay": {"type": "number"},
        "fontSize": {"type": "string"},
        "fontWeight": {"type": "string"},
        "color": {"type": "string"},
        "backgroundColor": {"type": "string"}
    }
    props.update(get_common_css_props())
    
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string", "enum": ["GlitchText"]},
            "props": {
                "type": "object",
                "properties": props
            },
            "children": children_schema
        },
        "required": ["name"]
    }


def build_element_object_schema(nesting_level=3):
    """
    Builds the complete ElementObject schema with anyOf for all element types.
    
    Args:
        nesting_level: How many levels deep to allow nesting (default: 3)
    
    Returns:
        Complete schema dictionary with recursive nesting
    """
    
    def build_level(current_level):
        """Recursively build schema levels"""
        
        if current_level == 0:
            # Deepest level - children can only be strings
            children_schema = {
                "type": "array",
                "items": {"type": "string"}
            }
        else:
            # Higher levels - children can be strings or nested elements
            next_level_elements = build_level(current_level - 1)
            children_schema = {
                "type": "array",
                "items": {
                    "anyOf": [
                        {"type": "string"},
                        next_level_elements
                    ]
                }
            }
        
        # Build anyOf array with all element types
        element_schemas = [
            # Media components
            get_video_element_schema(children_schema),
            get_audio_element_schema(children_schema),
            get_img_element_schema(children_schema),
            
            # Container component
            get_absolute_fill_element_schema(children_schema),
            
            # HTML elements (relevant for video compositions)
            get_html_element_schema("div", children_schema),
            get_html_element_schema("span", children_schema),
            get_html_element_schema("h1", children_schema),
            get_html_element_schema("h2", children_schema),
            get_html_element_schema("h3", children_schema),
            get_html_element_schema("p", children_schema),
            
            # Text animation components
            get_split_text_element_schema(children_schema),
            get_blur_text_element_schema(children_schema),
            get_typewriter_text_element_schema(children_schema),
            get_shuffle_element_schema(children_schema),
            get_gradient_text_element_schema(children_schema),
            get_decrypted_text_element_schema(children_schema),
            get_true_focus_element_schema(children_schema),
            get_glitch_text_element_schema(children_schema),
        ]
        
        return {
            "anyOf": element_schemas
        }
    
    return build_level(nesting_level)
