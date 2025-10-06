"""
Element String Schema Module

Minimal schema with string-based element definitions.
Each element is a semicolon-separated string with all documentation in description field.
"""

def build_simple_element_schema():
    """
    Minimal string-based element schema with comprehensive description.
    
    LLM generates strings in format: "ComponentName;id:value;parent:value;prop:value;..."
    Parser (to be implemented) will convert strings to element objects.
    """
    return {
        "type": "object",
        "properties": {
            "elements": {
                "type": "array",
                "description": """Array of element definitions. Each element is a semicolon-separated string in format:
ComponentName;id:uniqueId;parent:parentId;property:value;property:value;text:content

COMPONENTS (21 types for video composition):
- AbsoluteFill: Full-screen positioned container (use as root)
- Video: Video element (props: src, volume, startFrom, endAt, muted, playbackRate)
- Audio: Audio element (props: src, volume, startFrom, endAt, muted)
- Img: Image element (props: src)
- OffthreadVideo: Offthread video for performance (props: src, volume, startFrom, endAt, muted)
- Sequence: Timeline sequence container (props: from, durationInFrames)
- Series: Series animation container
- div, span: Generic containers for grouping and styling
- h1, h2, h3, p: Text heading and paragraph elements
- SplitText: Split text animation (props: text, animateBy [word/letter/line], direction, delay, duration)
- BlurText: Blur fade animation (props: text, delay, direction, duration)
- TypewriterText: Typewriter effect (props: text, typingSpeed, showCursor)
- Shuffle: Shuffle text animation (props: text, shuffleDirection)
- GradientText: Gradient text animation (props: text, colors array)
- DecryptedText: Decrypt text animation (props: text, animationSpeed)
- TrueFocus: Focus blur animation (props: text)
- GlitchText: Glitch text animation (props: text, speed)

PROPERTIES (use camelCase, all optional except id and parent):

Layout & Positioning:
- display: CSS display mode (flex, block, inline-flex, grid, none)
- position: CSS position (absolute, relative, fixed, sticky)
- top, bottom, left, right: Position offsets (0, 50%, 10px, 5vh)
- width, height: Dimensions (100%, 500px, 50vw, auto)

Flexbox:
- flexDirection: row, column, row-reverse, column-reverse
- justifyContent: center, flex-start, flex-end, space-between, space-around
- alignItems: center, flex-start, flex-end, stretch, baseline
- gap: Space between items (10px, 1rem)

Spacing:
- margin: All sides (10px, 20px 10px, 0 auto)
- marginTop, marginBottom: Individual margins (10px, 1rem)
- padding: Inner spacing (20px, 1rem 2rem)

Typography:
- fontSize: Font size (16px, 1.5rem, 3vw)
- fontFamily: Font name (Arial, Helvetica, Inter, monospace)
- fontWeight: Weight (400, 500, 600, 700, 800, bold, normal)
- fontStyle: Style (normal, italic)
- textAlign: Alignment (left, center, right, justify)
- lineHeight: Line spacing (1.5, 2, 24px)
- letterSpacing: Character spacing (0.05em, 2px)
- textTransform: Case (uppercase, lowercase, capitalize, none)

Colors:
- color: Text color (#fff, #000, rgb(255,0,0), rgba(255,0,0,0.5))
- backgroundColor: Background color (same formats)
- background: Complex backgrounds (linear-gradient(to right, #ff0000, #0000ff), url(image.jpg))

Visual Effects:
- opacity: Transparency 0-1 (0.5, 0.8, 1)
- transform: CSS transforms (translate(-50%, -50%), rotate(45deg), scale(1.2))
- textShadow: Text shadow (2px 2px 4px rgba(0,0,0,0.5))
- boxShadow: Box shadow (0px 4px 8px rgba(0,0,0,0.2))
- filter: CSS filters (blur(5px), brightness(1.2), grayscale(100%))

Borders:
- border: Border style (1px solid #fff, 2px dashed red)
- borderRadius: Corner radius (8px, 50%, 4px 8px)

Media Properties (Video/Audio/Img):
- src: File path (/video.mp4, /audio.mp3, /image.jpg) - REQUIRED for media
- volume: Audio level 0-1 (0.5, 0.8, 1)
- startFrom: Start time in frames or seconds
- endAt: End time in frames or seconds
- muted: true or false
- playbackRate: Speed (0.5, 1, 1.5, 2)

Animation Properties:
- text: Text content for text components
- animateBy: word, letter, or line (for SplitText)
- direction: up, down, left, right (animation direction)
- delay: Animation delay in seconds
- duration: Animation duration in seconds
- speed: Animation speed multiplier
- typingSpeed: Typing speed for TypewriterText
- showCursor: true/false for TypewriterText cursor
- shuffleDirection: Shuffle direction for Shuffle
- colors: Array notation for GradientText - colors:[#ff0000,#00ff00,#0000ff]
- animationSpeed: Speed for DecryptedText

REQUIRED FIELDS:
- id: Unique identifier (must be unique across all elements)
- parent: Parent element id (use "null" for root element)

FORMAT RULES:
- Semicolons separate all properties
- Format: property:value
- Use camelCase for property names
- Colors can use # or rgb/rgba with commas inside
- Complex CSS values (transforms, gradients) work with commas inside
- Text content: text:Your text here (no quotes needed, can contain spaces)
- Arrays: colors:[#ff0000,#00ff00] (square brackets, no spaces)

EXAMPLES:
"AbsoluteFill;id:root;parent:null;backgroundColor:#000;display:flex;justifyContent:center;alignItems:center"
"h1;id:title;parent:root;fontSize:48px;color:#fff;fontWeight:700;textAlign:center;text:Hello World"
"Video;id:vid;parent:container;src:/video.mp4;volume:0.8;startFrom:0;endAt:10;width:100%;height:100%"
"div;id:box;parent:root;background:linear-gradient(to right, #ff0000, #0000ff);padding:20px;borderRadius:8px"
"BlurText;id:blur1;parent:root;text:Fade In Text;fontSize:32px;delay:0.5;duration:1;direction:up;color:#fff"
"GradientText;id:grad1;parent:root;text:Colorful;fontSize:64px;colors:[#ff0000,#00ff00,#0000ff];animationSpeed:2"
"div;id:centered;parent:root;position:absolute;top:50%;left:50%;transform:translate(-50%, -50%);width:80%"
""",
                "items": {
                    "type": "string"
                }
            }
        },
        "required": ["elements"]
    }
