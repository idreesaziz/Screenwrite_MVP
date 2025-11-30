# Generate Media (Atomic Request)

**When to Use:**
- User directly requests generating NEW media from scratch: **image**, **video**, **logo**, or **voiceover/audio**
- Simple atomic request with no dependencies or complex workflow
- Examples:
  - "generate a sunset image"
  - "create a video of dancing robots"
  - "make a logo for a coffee shop"
  - "generate a voiceover saying 'welcome to our show'"

**User Request:** "generate a sunset image" or "create a video of dancing robots" or "make a logo"

**Complete Flow:**

1. **INFO**

```json
{
  "type": "info",
  "content": "I will generate a sunset image for you."
}
```

2. **GENERATE** - Image generation

```json
{
  "type": "generate",
  "content": "Generating a sunset beach image.",
  "content_type": "image",
  "prompt": "16:9 photo of a golden-hour beach, warm orange and pink sky (#FF6B35, #FFB6C1), calm ocean, soft sand, professional photography",
  "suggestedName": "sunset-beach"
}
```

3. **CHAT**

```json
{
  "type": "chat",
  "content": "I've generated 'sunset-beach.png' for you. It's now in your media bin. Would you like to use it in your composition, or would you like me to generate something different?"
}
```

**→ HALT** (Workflow stops, wait for user's next instruction)

---

## Alternative: Video Generation

**User Request:** "generate a video of dancing robots"

**Complete Flow:**

1. **INFO**

```json
{
  "type": "info",
  "content": "I will generate a video of dancing robots."
}
```

2. **GENERATE** - Video generation

```json
{
  "type": "generate",
  "content": "Generating an 8-second video of dancing robots.",
  "content_type": "video",
  "prompt": "8s video of cute friendly robots dancing in synchronized choreography, colorful LED lights, dark studio background, energetic movement",
  "suggestedName": "dancing-robots"
}
```

3. **CHAT**

```json
{
  "type": "chat",
  "content": "I've generated 'dancing-robots.mp4' for you (8 seconds). It's now in your media bin. Would you like to use it in your composition?"
}
```

**→ HALT** (Workflow stops, wait for user's next instruction)

---

## Alternative: Logo Generation

**User Request:** "create a logo" or "generate a logo for my brand"

**Complete Flow:**
1. **INFO**

```json
{
  "type": "info",
  "content": "I will generate a logo for you."
}
```

2. **GENERATE** - Logo generation

```json
{
  "type": "generate",
  "content": "Generating a logo with transparent background.",
  "content_type": "logo",
  "prompt": "[subject] [style-descriptor]",
  "suggestedName": "[descriptive-name]-logo"
}
```
   
   **Note:** Logo prompts are SHORT (2-5 words). System automatically handles:
   - Transparent background (green chroma key removal)
   - Professional styling and centering
   - 1:1 aspect ratio (square)
   - Clean edges suitable for overlays

3. **CHAT**

```json
{
  "type": "chat",
  "content": "I've generated '[descriptive-name]-logo.png' for you with a transparent background. It's now in your media bin and ready to use as an overlay. Would you like to place it on the timeline?"
}
```

**→ HALT** (Workflow stops, wait for user's next instruction)

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
- SHORT simple prompts (e.g., "[subject] [style]")
- Transparent background (PNG)
- Perfect for overlays on videos/images

**Audio/Voiceover (content_type: "audio"):**
- Prompt is the TEXT TO SPEAK (not a description)
- Returns duration in seconds (critical for timeline sync)
- Optional: voice_settings for voice_id, language_code, style_prompt, speaking_rate, pitch
- Default voice: "Aoede" (Gemini voice), language: "en-US"
