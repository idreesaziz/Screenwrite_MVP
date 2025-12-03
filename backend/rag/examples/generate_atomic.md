# Generate Media (Atomic Request)

**When to Use:**
- User directly requests generating NEW media from scratch: **image**, **video**, or **logo**
- Simple atomic request with no dependencies or complex workflow
- Examples: "generate a sunset image", "create a video of dancing robots", "make a logo for a coffee shop"

**User Request:** "generate a sunset image" or "create a video of dancing robots" or "make a logo"

**Complete Flow:**

1. **AGENT - INFO** (Announce next action)
```json
{
  "type": "info",
  "content": "I will generate a sunset image for you."
}
```

2. **AGENT - GENERATE** (Create media)
```json
{
  "type": "generate",
  "content": "Generating a sunset beach image.",
  "content_type": "image",
  "prompt": "16:9 photo of a golden-hour beach, warm orange and pink sky (#FF6B35, #FFB6C1), calm ocean, soft sand, professional photography",
  "suggestedName": "sunset-beach"
}
```

3. **SYSTEM - Generation Result** (automatic, media added to bin)
```
Successfully generated image: sunset-beach. The image has been added to your media library.
```

4. **AGENT - SLEEP** (Pause workflow, wait for user)
```json
{
  "type": "sleep",
  "content": "I've generated 'sunset-beach' for you. It's now in your media bin. Would you like to use it in your composition, or would you like me to generate something different?"
}
```

---

## Alternative: Video Generation

**User Request:** "generate a video of dancing robots"

1. **AGENT - INFO**
```json
{
  "type": "info",
  "content": "I will generate a video of dancing robots."
}
```

2. **AGENT - GENERATE**
```json
{
  "type": "generate",
  "content": "Generating an 8-second video of dancing robots.",
  "content_type": "video",
  "prompt": "8s video of cute friendly robots dancing in synchronized choreography, colorful LED lights, dark studio background, energetic movement",
  "suggestedName": "dancing-robots"
}
```

3. **SYSTEM - Generation Result**
```
Successfully generated video: dancing-robots. The video has been added to your media library.
```

4. **AGENT - SLEEP**
```json
{
  "type": "sleep",
  "content": "I've generated 'dancing-robots' for you (8 seconds). It's now in your media bin. Would you like to use it in your composition?"
}
```

---

## Alternative: Logo Generation

**User Request:** "create a logo" or "generate a logo for my brand"

1. **AGENT - INFO**
```json
{
  "type": "info",
  "content": "I will generate a logo for you."
}
```

2. **AGENT - GENERATE**
```json
{
  "type": "generate",
  "content": "Generating a logo with transparent background.",
  "content_type": "logo",
  "prompt": "coffee cup minimalistic",
  "suggestedName": "coffee-logo"
}
```

3. **SYSTEM - Generation Result**
```
Successfully generated logo: coffee-logo. The logo has been added to your media library.
```

4. **AGENT - SLEEP**
```json
{
  "type": "sleep",
  "content": "I've generated 'coffee-logo' for you with a transparent background. It's now in your media bin and ready to use as an overlay. Would you like to place it on the timeline?"
}
```

---

## Key Differences

**Images (content_type: "image"):**
- 16:9 aspect ratio
- Detailed prompts with colors, composition, lighting
- Opaque background

**Videos (content_type: "video"):**
- 8 seconds duration
- Detailed prompts with motion, camera work, lighting, scene description
- 16:9 aspect ratio
- Generate NEW video from text description (not from existing image)

**Logos (content_type: "logo"):**
- 1:1 aspect ratio (square)
- SHORT simple prompts (e.g., "coffee cup minimalistic")
- Transparent background (PNG)
- Perfect for overlays on videos/images

---

## Key Points:
- System automatically adds generated media to library
- Agent uses SLEEP to pause and wait for user input
- Do not respond to system generation confirmations - they're tool outputs
