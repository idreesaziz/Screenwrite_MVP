# Animate Image to Video

**When to Use:**
- **CRITICAL TRIGGER PHRASES (always match this example):**
  - "animate this image"
  - "make this photo move"
  - "bring this image to life"
  - "turn [image-name] into a video"
  - "animate [image-name]"
  - "animate this image saying/screaming/with [any audio description]"
- User wants to transform an existing image in their media bin into a video with motion/camera movement
- This is NOT generating a brand new video from text, but animating an existing image

**User Request:** "animate this image" or "make screenshot_from_2025 move" or "animate this image screaming hello"

**Complete Flow:**

1. **INFO**

```json
{
  "type": "info",
  "content": "I will animate that image into a video for you."
}
```

2. **GENERATE** - Video generation with reference image

```json
{
  "type": "generate",
  "content": "Generating an 8-second video from your image.",
  "content_type": "video",
  "prompt": "8s video: [describe camera movement, motion effects], [if user requested audio: include audio description here]",
  "reference_image_url": "https://storage.googleapis.com/screenwrite-media/user_xxx/session_yyy/image_name",
  "suggestedName": "animated-photo"
}
```
   
   **CRITICAL NOTES:**
   - `reference_image_url` MUST be the full GCS URL from the image in media bin
   - Prompt describes MOTION/CAMERA WORK, NOT content (content comes from the reference image)
   - **VIDEO GENERATION INCLUDES AUDIO AUTOMATICALLY** - if user wants audio/voiceover, add it directly in the prompt
   - Focus on: camera movement, lighting changes, motion style, depth effects, and audio if requested
   - AVOID describing the scene/content (that's already in the image)

3. **CHAT**

```json
{
  "type": "chat",
  "content": "I've generated '[name]' from your image (8 seconds). It's now in your media bin. Would you like to add it to your composition?"
}
```

**→ HALT** (Workflow stops, wait for user's next instruction)

---

## Key Points

**This workflow is for:**
- Animating existing images from media bin
- Adding motion/camera effects to static photos
- Creating videos from reference images
- Adding audio/voiceover to animated images

**This workflow is NOT for:**
- Generating brand new videos from text descriptions (use generate_atomic.md instead)
- Creating compositions with text overlays (use composition workflows)
- Editing existing videos (use edit workflows)

**Technical Requirements:**
- Image must already exist in user's media bin
- Must extract the full GCS URL for reference_image_url
- Prompt focuses on motion/camera work and optional audio, not content description
- Always 8 seconds duration
- Returns a new video file in media bin
