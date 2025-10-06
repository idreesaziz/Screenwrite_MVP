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
                            "description": "Unique identifier for this element. Must be unique across all elements. Used by other elements' parentId to reference this element. Example: 'root', 'title-text', 'bg-video-1'"
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
                            "description": "Component type. Use 'AbsoluteFill' for root container, 'Video'/'Audio'/'Img' for media (requires 'src' prop), 'div' for layout containers, 'h1'/'h2'/'h3'/'p'/'span' for text display, or text animation components like 'SplitText'/'GradientText' (requires 'text' prop). Example: 'AbsoluteFill' for full-screen container, 'h1' for title text"
                        },
                        "parentId": {
                            "type": "string",
                            "description": "ID of parent element to nest this element inside. MUST match an existing element's 'id'. Use null ONLY for the root element (typically AbsoluteFill). All other elements must have a valid parentId. Example: 'root' to nest inside element with id='root'"
                        },
                        "props": {
                            "type": "object",
                            "properties": {
                                # === LAYOUT & POSITIONING ===
                                "display": {
                                    "type": "string",
                                    "description": "CSS display mode controlling layout method. Use 'flex' for flexbox layouts (enables justifyContent/alignItems), 'block' for block-level elements, 'inline-block' for inline with dimensions. Example: 'flex' to center children"
                                },
                                "position": {
                                    "type": "string",
                                    "description": "CSS positioning type. Use 'absolute' with top/left/bottom/right for precise placement, 'relative' for offset from normal position. Absolute positioning required for layering elements. Example: 'absolute' with top='50%' and left='50%' for centering"
                                },
                                "top": {
                                    "type": "string",
                                    "description": "Distance from top edge (requires position='absolute' or 'relative'). Use with bottom for vertical sizing, or with transform for centering. Example: '10%' for 10% from top, '50%' with transform='translateY(-50%)' for vertical center"
                                },
                                "bottom": {
                                    "type": "string",
                                    "description": "Distance from bottom edge (requires position='absolute' or 'relative'). Useful for anchoring text/elements to bottom of screen. Example: '10%' to place element 10% from bottom"
                                },
                                "left": {
                                    "type": "string",
                                    "description": "Distance from left edge (requires position='absolute' or 'relative'). Use with right for horizontal sizing, or with transform for centering. Example: '50%' with transform='translateX(-50%)' for horizontal center"
                                },
                                "right": {
                                    "type": "string",
                                    "description": "Distance from right edge (requires position='absolute' or 'relative'). Useful for right-aligned elements. Example: '20px' to place 20px from right edge"
                                },
                                "width": {
                                    "type": "string",
                                    "description": "Element width. Use '100%' for full width, pixel values for fixed width, 'auto' for content-based width. Example: '100%' for full-width container, '800px' for fixed-width overlay"
                                },
                                "height": {
                                    "type": "string",
                                    "description": "Element height. Use '100%' for full height, pixel values for fixed height, 'auto' for content-based height. Example: '100%' for full-height container, '200px' for fixed-height text area"
                                },
                                
                                # === FLEXBOX LAYOUT ===
                                "flexDirection": {
                                    "type": "string",
                                    "description": "Direction of flex items (requires display='flex'). Use 'row' for horizontal layout, 'column' for vertical stacking. Affects how justifyContent and alignItems work. Example: 'column' to stack title and subtitle vertically"
                                },
                                "justifyContent": {
                                    "type": "string",
                                    "description": "Main axis alignment (requires display='flex'). For flexDirection='row': horizontal alignment. For 'column': vertical alignment. Use 'center' to center items, 'space-between' to space items evenly. Example: 'center' to center text horizontally in a row layout"
                                },
                                "alignItems": {
                                    "type": "string",
                                    "description": "Cross axis alignment (requires display='flex'). For flexDirection='row': vertical alignment. For 'column': horizontal alignment. Use 'center' to center items on cross axis. Example: 'center' to vertically center text in a row layout"
                                },
                                "gap": {
                                    "type": "string",
                                    "description": "Spacing between flex children (requires display='flex'). Adds uniform space between items without using margins. Example: '20px' to add 20px space between stacked text elements"
                                },
                                
                                # === SPACING ===
                                "margin": {
                                    "type": "string",
                                    "description": "Outer spacing around element to push other elements away. Can specify all sides at once. Shorthand: 'top right bottom left' or 'vertical horizontal'. Use to separate elements vertically or horizontally. Example: '20px' for 20px on all sides, '10px 20px' for 10px top/bottom and 20px left/right, '10px 20px 30px 40px' for top right bottom left"
                                },
                                "marginTop": {
                                    "type": "string",
                                    "description": "Outer spacing above element. Pushes element down from element above it. Use to add space above specific element without affecting other sides. Example: '30px' to add space above subtitle, '50px' to push element down from top"
                                },
                                "marginBottom": {
                                    "type": "string",
                                    "description": "Outer spacing below element. Pushes next element down. Use to add space after specific element without affecting other sides. Example: '40px' to add space after title before subtitle, '20px' to separate paragraphs"
                                },
                                "padding": {
                                    "type": "string",
                                    "description": "Inner spacing inside element between border and content. Expands element size. Can specify all sides at once. Use to add breathing room around text inside containers. Example: '20px' for 20px padding on all sides, '15px 30px' for 15px top/bottom and 30px left/right, '10px 20px 10px 20px' for top right bottom left"
                                },
                                
                                # === TYPOGRAPHY ===
                                "fontSize": {
                                    "type": "string",
                                    "description": "Text size. Use pixels for fixed size, viewport units for responsive. Larger values for titles, smaller for body text. Example: '48px' for main title, '24px' for subtitle, '16px' for body text"
                                },
                                "fontFamily": {
                                    "type": "string",
                                    "description": "Font typeface with fallbacks. Always include generic family (sans-serif, serif, monospace) as fallback. Example: 'Arial, Helvetica, sans-serif' for clean modern look, 'Georgia, serif' for elegant text"
                                },
                                "fontWeight": {
                                    "type": "string",
                                    "description": "Text thickness/boldness. Use 'bold' or '700' for emphasis, 'normal' or '400' for regular text, '300' for light text. Example: 'bold' for titles, '400' for body text"
                                },
                                "fontStyle": {
                                    "type": "string",
                                    "description": "Text style variant. Use 'italic' for emphasis or quotes, 'normal' for regular text. Example: 'italic' for subtitle or quote text"
                                },
                                "textAlign": {
                                    "type": "string",
                                    "description": "Horizontal text alignment within element. Use 'center' for centered text (common for titles), 'left' for body text, 'right' for right-aligned elements. Example: 'center' for centered title"
                                },
                                "lineHeight": {
                                    "type": "string",
                                    "description": "Vertical spacing between lines of text. Use unitless numbers (1.5 = 150% of font size) or fixed values. Higher values add more space. Example: '1.5' for readable multi-line text, '1' for tight single-line titles"
                                },
                                "letterSpacing": {
                                    "type": "string",
                                    "description": "Horizontal spacing between characters. Positive values spread text out, negative values compress. Use for stylistic text effects. Example: '2px' for spaced-out title effect, '0.05em' for slightly looser text"
                                },
                                "textTransform": {
                                    "type": "string",
                                    "description": "Text case transformation applied automatically. Use 'uppercase' for all-caps titles, 'capitalize' for title case, 'none' for original case. Example: 'uppercase' to convert 'hello world' to 'HELLO WORLD'"
                                },
                                
                                # === COLORS & BACKGROUNDS ===
                                "color": {
                                    "type": "string",
                                    "description": "Text color in hex, rgb, or rgba format. Use hex for solid colors, rgba for transparency. White text on dark backgrounds is common for readability. Example: '#ffffff' for white text, 'rgba(255,255,255,0.9)' for semi-transparent white"
                                },
                                "backgroundColor": {
                                    "type": "string",
                                    "description": "Solid background color for element. Use hex for solid colors, rgba for semi-transparent backgrounds (useful for overlays on video). Example: '#000000' for black background, 'rgba(0,0,0,0.7)' for semi-transparent dark overlay"
                                },
                                "background": {
                                    "type": "string",
                                    "description": "Advanced background with gradients or images. Use 'linear-gradient' for color transitions, 'radial-gradient' for circular gradients. Example: 'linear-gradient(to bottom, #1a1a2e, #16213e)' for gradient background, 'linear-gradient(90deg, #ff0000 0%, #00ff00 100%)' for left-to-right gradient"
                                },
                                
                                # === VISUAL EFFECTS ===
                                "opacity": {
                                    "type": "string",
                                    "description": "Element transparency from '0' (invisible) to '1' (fully opaque). Affects entire element including children. Use for fade effects or subtle overlays. Example: '0.8' for slightly transparent element, '0.5' for half-transparent overlay"
                                },
                                "transform": {
                                    "type": "string",
                                    "description": "CSS transformations for positioning, scaling, or rotation. CRITICAL for centering: use 'translate(-50%, -50%)' with top='50%' left='50%'. Can combine multiple transforms. Example: 'translate(-50%, -50%)' to center element, 'scale(1.2)' to enlarge by 20%, 'rotate(45deg)' to rotate"
                                },
                                "textShadow": {
                                    "type": "string",
                                    "description": "Shadow effect behind text for depth or readability. Format: 'x-offset y-offset blur-radius color'. Use for text on busy backgrounds. Example: '2px 2px 4px rgba(0,0,0,0.8)' for subtle shadow, '0 0 20px #00ff00' for glow effect"
                                },
                                "boxShadow": {
                                    "type": "string",
                                    "description": "Shadow effect around element box for depth or elevation. Format: 'x-offset y-offset blur-radius spread color'. Use for card-like elements. Example: '0 4px 6px rgba(0,0,0,0.3)' for subtle shadow, '0 10px 30px rgba(0,0,0,0.5)' for elevated effect"
                                },
                                "filter": {
                                    "type": "string",
                                    "description": "Visual filters applied to element. Can combine multiple filters with spaces. Use for effects on videos or images. Example: 'blur(5px)' to blur element, 'brightness(120%) contrast(110%)' to enhance video, 'grayscale(100%)' for black and white"
                                },
                                
                                # === BORDERS ===
                                "border": {
                                    "type": "string",
                                    "description": "Border around element. Format: 'width style color'. Use for outlining text boxes or containers. Example: '2px solid #ffffff' for white border, '3px dashed rgba(255,0,0,0.8)' for red dashed border"
                                },
                                "borderRadius": {
                                    "type": "string",
                                    "description": "Rounded corners for element. Use pixels for subtle rounding, percentage for circular shapes. Example: '10px' for slightly rounded corners, '50%' for circular element, '20px 20px 0 0' for rounded top corners only"
                                },
                                
                                # === MEDIA COMPONENT PROPS (Video/Audio/Img) ===
                                "src": {
                                    "type": "string",
                                    "description": "REQUIRED for Video/Audio/Img/OffthreadVideo: Source URL or media ID. Use 'mediaId:abc123' format to reference media from media_library, or direct URL for external media. This is MANDATORY for all media components. Example: 'mediaId:user-uploaded-video' to use media from library, 'https://example.com/video.mp4' for external video, '/assets/image.jpg' for local file"
                                },
                                "volume": {
                                    "type": "number",
                                    "description": "Audio volume level from 0.0 (silent) to 1.0 (full volume). Only works on Audio and Video components. Use to balance multiple audio tracks or reduce background music. Example: 0.8 for 80% volume, 0.3 for quiet background music, 1.0 for full volume narration"
                                },
                                "startFrom": {
                                    "type": "number",
                                    "description": "Time in seconds to start playing media from. Use to trim beginning of video/audio clip. Useful for cutting intros or silent parts. Example: 5 to skip first 5 seconds, 10.5 to start at 10.5 seconds, 0 to start from beginning"
                                },
                                "endAt": {
                                    "type": "number",
                                    "description": "Time in seconds to stop playing media at. Use with startFrom to extract specific segment of clip. Useful for using only part of a video. Example: 15 to end at 15 seconds, 30.5 for 30.5-second mark. If startFrom=5 and endAt=15, plays 10 seconds"
                                },
                                "muted": {
                                    "type": "boolean",
                                    "description": "Whether to mute audio of Video/Audio component. Use true for background video without sound or when using separate audio track. Example: true to mute background video, false to keep audio"
                                },

                                "playbackRate": {
                                    "type": "number",
                                    "description": "Speed multiplier for playback. Values >1 speed up, values <1 slow down. Affects both video and audio pitch. Example: 2.0 for 2x speed (double-time), 0.5 for slow motion, 1.5 for slightly faster, 1.0 for normal speed"
                                },
                                
                                # === TEXT ANIMATION PROPS ===
                                "text": {
                                    "type": "string",
                                    "description": "REQUIRED for text animation components: Text content to animate. Use for SplitText, TypewriterText, BlurText, Shuffle, GradientText, DecryptedText, GlitchText. This is MANDATORY for all text animation components. Example: 'Hello World' for simple text, 'Welcome to our video' for longer phrases"
                                },
                                "animateBy": {
                                    "type": "string",
                                    "description": "Animation granularity for SplitText/BlurText: how to split text for animation. 'characters' animates each letter, 'words' animates each word, 'lines' animates each line. Use 'characters' for dramatic letter-by-letter effects. Example: 'characters' for letter-by-letter reveal, 'words' for word-by-word appearance, 'lines' for line-by-line fade"
                                },
                                "direction": {
                                    "type": "string",
                                    "description": "Direction of animation entrance for SplitText/BlurText. Controls which side elements appear from. Use 'top' for slide-down effect, 'bottom' for slide-up. Example: 'top' for text sliding down into position, 'left' for text sliding from left, 'bottom' for text rising up"
                                },
                                "delay": {
                                    "type": "number",
                                    "description": "Delay in seconds before animation starts. Use to sequence multiple animations or sync with other elements. Works with all text animation components. Example: 0.5 to start after half second, 2.0 to delay 2 seconds, 0 to start immediately"
                                },
                                "duration": {
                                    "type": "number",
                                    "description": "Duration in seconds for EACH animated unit (character/word/line) to complete its animation. Total animation time = duration × number of units. Use shorter for snappy effects, longer for smooth transitions. Example: 0.5 for quick animations, 1.0 for moderate speed, 2.0 for slow dramatic effect"
                                },
                                "speed": {
                                    "type": "number",
                                    "description": "Speed multiplier for animation. Higher values make animation faster. Alternative to duration for controlling animation pace. Example: 1.0 for normal speed, 2.0 for double speed, 0.5 for half speed"
                                },
                                "typingSpeed": {
                                    "type": "number",
                                    "description": "REQUIRED for TypewriterText: Characters typed per second. Controls how fast the typewriter effect types out text. Higher = faster typing. Example: 10 for slow typing (10 chars/sec), 30 for medium speed, 60 for fast typing effect"
                                },
                                "showCursor": {
                                    "type": "boolean",
                                    "description": "Whether to show blinking cursor for TypewriterText component. Use true for authentic typewriter effect, false for just the typing animation. Example: true to show cursor, false to hide cursor"
                                },
                                "shuffleDirection": {
                                    "type": "string",
                                    "description": "Direction of shuffle reveal effect for Shuffle component. Controls which side the shuffled characters settle from. Example: 'left' for left-to-right reveal, 'right' for right-to-left reveal"
                                },
                                "colors": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    },
                                    "description": "REQUIRED for GradientText: Array of colors for gradient animation. Must have at least 2 colors. Colors cycle through creating animated gradient effect. Example: ['#ff0000', '#00ff00', '#0000ff'] for RGB gradient, ['#ff6b6b', '#4ecdc4', '#45b7d1'] for colorful gradient"
                                },
                                "animationSpeed": {
                                    "type": "number",
                                    "description": "Speed of color gradient animation for GradientText component. Higher values make gradient shift faster across text. Example: 1.0 for slow gradient shift, 5.0 for fast shifting colors, 10.0 for very rapid color animation"
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
