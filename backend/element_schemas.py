"""
Element Object Schema Module

Comprehensive flat element list structure with parent references.
Includes all component types and properties with detailed descriptions.
"""

def build_simple_element_schema():
    """
    Comprehensive flat element list schema with all component types and properties.
    
    Structure:
    {
      "elements": [
        {"id": "root", "name": "AbsoluteFill", "parentId": null, "props": {...}},
        {"id": "div1", "name": "div", "parentId": "root", "props": {...}},
        {"id": "text1", "name": "h1", "parentId": "div1", "props": {...}, "text": "Hello"}
      ]
    }
    
    All properties are defined with types and descriptions for AI guidance.
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
                            "description": "Unique identifier for this element (e.g., 'root', 'title-1', 'bg-video')"
                        },
                        "name": {
                            "type": "string",
                            "enum": [
                                # Remotion media components
                                "Video", "Audio", "Img", "OffthreadVideo",
                                # Remotion containers
                                "AbsoluteFill", "Sequence", "Series",
                                # Essential HTML elements for video composition
                                "div", "span", "h1", "h2", "h3", "p",
                                # Text animation components
                                "SplitText", "BlurText", "TypewriterText", "Shuffle", 
                                "GradientText", "DecryptedText", "TrueFocus", "GlitchText"
                            ],
                            "description": "Component type for video composition: Media (Video, Audio, Img), Containers (AbsoluteFill, div), Text (h1, p, span), or Text Animations (SplitText, GradientText, etc.)"
                        },
                        "parentId": {
                            "type": "string",
                            "description": "ID of parent element. Use null for root element only."
                        },
                        "props": {
                            "type": "object",
                            "properties": {
                                # === LAYOUT & POSITIONING ===
                                "display": {
                                    "type": "string",
                                    "description": "CSS display mode: 'flex', 'block', 'inline-block', 'grid', 'none', etc."
                                },
                                "position": {
                                    "type": "string",
                                    "description": "CSS position: 'absolute', 'relative', 'fixed', 'static', 'sticky'"
                                },
                                "top": {
                                    "type": "string",
                                    "description": "Distance from top edge in CSS units: '0', '50%', '20px', '10vh'"
                                },
                                "bottom": {
                                    "type": "string",
                                    "description": "Distance from bottom edge in CSS units: '0', '10%', '20px'"
                                },
                                "left": {
                                    "type": "string",
                                    "description": "Distance from left edge in CSS units: '0', '50%', '20px', '10vw'"
                                },
                                "right": {
                                    "type": "string",
                                    "description": "Distance from right edge in CSS units: '0', '10%', '20px'"
                                },
                                "width": {
                                    "type": "string",
                                    "description": "Element width in CSS units: '100%', '500px', '50vw', 'auto'"
                                },
                                "height": {
                                    "type": "string",
                                    "description": "Element height in CSS units: '100%', '300px', '50vh', 'auto'"
                                },
                                
                                # === FLEXBOX LAYOUT ===
                                "flexDirection": {
                                    "type": "string",
                                    "description": "Flex container direction: 'row', 'column', 'row-reverse', 'column-reverse'"
                                },
                                "justifyContent": {
                                    "type": "string",
                                    "description": "Horizontal alignment in flex: 'center', 'flex-start', 'flex-end', 'space-between', 'space-around'"
                                },
                                "alignItems": {
                                    "type": "string",
                                    "description": "Vertical alignment in flex: 'center', 'flex-start', 'flex-end', 'stretch', 'baseline'"
                                },
                                "gap": {
                                    "type": "string",
                                    "description": "Space between flex/grid items: '10px', '1rem', '20px'"
                                },
                                
                                # === SPACING ===
                                "margin": {
                                    "type": "string",
                                    "description": "Outer spacing around element: '10px', '20px 10px', '1rem 2rem 1rem 2rem'"
                                },
                                "marginTop": {
                                    "type": "string",
                                    "description": "Top margin: '10px', '1rem', '5%'"
                                },
                                "marginBottom": {
                                    "type": "string",
                                    "description": "Bottom margin: '10px', '1rem', '5%'"
                                },
                                "padding": {
                                    "type": "string",
                                    "description": "Inner spacing inside element: '10px', '20px 10px', '1rem'"
                                },
                                
                                # === TYPOGRAPHY ===
                                "fontSize": {
                                    "type": "string",
                                    "description": "Font size in CSS units: '16px', '1.5rem', '24px', '3vw'"
                                },
                                "fontFamily": {
                                    "type": "string",
                                    "description": "Font family: 'Arial, sans-serif', 'Georgia, serif', 'monospace'"
                                },
                                "fontWeight": {
                                    "type": "string",
                                    "description": "Font weight: 'normal', 'bold', '100', '400', '700', '900'"
                                },
                                "fontStyle": {
                                    "type": "string",
                                    "description": "Font style: 'normal', 'italic', 'oblique'"
                                },
                                "textAlign": {
                                    "type": "string",
                                    "description": "Text alignment: 'left', 'center', 'right', 'justify'"
                                },
                                "lineHeight": {
                                    "type": "string",
                                    "description": "Line height: '1.5', '2', '24px', 'normal'"
                                },
                                "letterSpacing": {
                                    "type": "string",
                                    "description": "Space between characters: '0.05em', '2px', 'normal'"
                                },
                                "textTransform": {
                                    "type": "string",
                                    "description": "Text case transformation: 'uppercase', 'lowercase', 'capitalize', 'none'"
                                },
                                
                                # === COLORS & BACKGROUNDS ===
                                "color": {
                                    "type": "string",
                                    "description": "Text color: '#ffffff', '#000', 'rgb(255,0,0)', 'rgba(0,0,0,0.5)'"
                                },
                                "backgroundColor": {
                                    "type": "string",
                                    "description": "Background color: '#1a1a1a', 'rgba(0,0,0,0.8)', 'transparent'"
                                },
                                "background": {
                                    "type": "string",
                                    "description": "Background (color/gradient/image): 'linear-gradient(to right, #ff0000, #0000ff)', 'url(image.jpg)'"
                                },
                                
                                # === VISUAL EFFECTS ===
                                "opacity": {
                                    "type": "string",
                                    "description": "Transparency level: '1' (opaque), '0.5' (semi-transparent), '0' (invisible)"
                                },
                                "transform": {
                                    "type": "string",
                                    "description": "CSS transforms: 'translateX(50px)', 'scale(1.5)', 'rotate(45deg)', 'translate(-50%, -50%)'"
                                },
                                "textShadow": {
                                    "type": "string",
                                    "description": "Text shadow effect: '2px 2px 4px rgba(0,0,0,0.5)', '0 0 10px #00ff00'"
                                },
                                "boxShadow": {
                                    "type": "string",
                                    "description": "Box shadow effect: '0 4px 6px rgba(0,0,0,0.1)', 'inset 0 0 10px #000'"
                                },
                                "filter": {
                                    "type": "string",
                                    "description": "CSS filters: 'blur(5px)', 'brightness(150%)', 'contrast(200%)', 'grayscale(100%)'"
                                },
                                
                                # === BORDERS ===
                                "border": {
                                    "type": "string",
                                    "description": "Border style: '1px solid #fff', '2px dashed rgba(255,0,0,0.5)'"
                                },
                                "borderRadius": {
                                    "type": "string",
                                    "description": "Corner rounding: '5px', '50%', '10px 20px', '1rem'"
                                },
                                
                                # === MEDIA COMPONENT PROPS (Video/Audio/Img) ===
                                "src": {
                                    "type": "string",
                                    "description": "Source URL for Video/Audio/Img/IFrame components. MUST be full URL path from media library."
                                },
                                "volume": {
                                    "type": "number",
                                    "description": "Audio volume for Video/Audio components: 0.0 (mute) to 1.0 (full volume)"
                                },
                                "startFrom": {
                                    "type": "number",
                                    "description": "Start time in seconds for Video/Audio trimming (e.g., 5 starts at 5-second mark)"
                                },
                                "endAt": {
                                    "type": "number",
                                    "description": "End time in seconds for Video/Audio trimming (e.g., 10 ends at 10-second mark)"
                                },
                                "muted": {
                                    "type": "boolean",
                                    "description": "Mute audio for Video/Audio components: true or false"
                                },

                                "playbackRate": {
                                    "type": "number",
                                    "description": "Playback speed: 0.5 (half speed), 1.0 (normal), 2.0 (double speed)"
                                },
                                
                                # === TEXT ANIMATION PROPS ===
                                "text": {
                                    "type": "string",
                                    "description": "Text content for text animation components (SplitText, TypewriterText, etc.)"
                                },
                                "animateBy": {
                                    "type": "string",
                                    "description": "Animation unit for SplitText/BlurText: 'characters', 'words', 'lines'"
                                },
                                "direction": {
                                    "type": "string",
                                    "description": "Animation direction for SplitText/BlurText: 'top', 'bottom', 'left', 'right'"
                                },
                                "delay": {
                                    "type": "number",
                                    "description": "Animation delay in seconds before starting"
                                },
                                "duration": {
                                    "type": "number",
                                    "description": "Animation duration in seconds for each element"
                                },
                                "speed": {
                                    "type": "number",
                                    "description": "Animation speed multiplier (higher = faster)"
                                },
                                "typingSpeed": {
                                    "type": "number",
                                    "description": "Characters per second for TypewriterText"
                                },
                                "showCursor": {
                                    "type": "boolean",
                                    "description": "Show blinking cursor for TypewriterText: true or false"
                                },
                                "shuffleDirection": {
                                    "type": "string",
                                    "description": "Shuffle animation direction: 'left', 'right'"
                                },
                                "colors": {
                                    "type": "array",
                                    "description": "Array of colors for GradientText: ['#ff0000', '#00ff00', '#0000ff']"
                                },
                                "animationSpeed": {
                                    "type": "number",
                                    "description": "Speed of gradient animation for GradientText"
                                }
                            },
                            "description": "Element properties: CSS styles, media properties (src, volume), and component-specific props"
                        },
                        "text": {
                            "type": "string",
                            "description": "Text content to display inside this element (for h1, p, span, etc.)"
                        }
                    },
                    "required": ["id", "name"]
                },
                "description": "Flat list of all elements in the composition tree. Build nesting using parentId references."
            }
        },
        "required": ["elements"]
    }
