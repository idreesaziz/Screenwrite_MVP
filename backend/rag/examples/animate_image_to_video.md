# Animate Image to Video

**When to Use:**
- User wants to transform an existing image in their media bin into a video with motion/camera movement
- CRITICAL TRIGGER PHRASES: "animate this image", "make this photo move", "bring this image to life", "turn [image-name] into a video"
- This is NOT generating a brand new video from text

**User Request:** "animate this image" or "make screenshot_from_2025 move"

**Complete Flow:**

1. **AGENT - INFO**
```json
{
  "type": "info",
  "content": "I will animate that image into a video for you."
}
```

2. **AGENT - GENERATE** (with reference image)
```json
{
  "type": "generate",
  "content": "Generating an 8-second video from your image.",
  "content_type": "video",
  "prompt": "8s video: slow zoom in with subtle camera pan, cinematic depth effect, professional lighting transitions",
  "reference_image_url": "https://storage.googleapis.com/screenwrite-media/user_xxx/session_yyy/image_name",
  "suggestedName": "animated-photo"
}
```

3. **SYSTEM - Generation Result**
```
Successfully generated video: animated-photo. The video has been added to your media library.
```

4. **AGENT - SLEEP**
```json
{
  "type": "sleep",
  "content": "I've generated 'animated-photo' from your image (8 seconds). It's now in your media bin. Would you like to add it to your composition?"
}
```

---

## Key Points:
- `reference_image_url`: Full GCS URL from the image in media bin
- Prompt describes MOTION/CAMERA WORK, NOT content (content comes from the reference image)
- Focus on: camera movement, lighting changes, motion style, depth effects
- Always 8 seconds duration
- Agent uses SLEEP to pause workflow
- Do not respond to system generation confirmations
