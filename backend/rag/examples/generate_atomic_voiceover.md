# Generate Voice-Over (Atomic Request)

**When to Use:**
- User directly requests voice-over narration generation
- Simple atomic request with no dependencies
- User provides or implies a text script to be spoken

**User Request:** "generate voice-over narration" or "add voice-over saying 'Welcome to our showcase'"

**Complete Flow:**

1. **AGENT - INFO**
```json
{
  "type": "info",
  "content": "I will generate voice-over narration for you."
}
```

2. **AGENT - GENERATE**
```json
{
  "type": "generate",
  "content": "Generating voice-over narration.",
  "content_type": "audio",
  "prompt": "Welcome to our product showcase. Today we're excited to introduce our latest innovation that will transform the way you work.",
  "suggestedName": "intro-narration",
  "voice_settings": {
    "voice_id": "Aoede",
    "language_code": "en-US",
    "style_prompt": "Speak with confidence and authority"
  }
}
```

3. **SYSTEM - Generation Result** (automatic)
```
Successfully generated audio: intro-narration (5.2 seconds). The audio has been added to your media library.
```

4. **AGENT - SLEEP**
```json
{
  "type": "sleep",
  "content": "I've generated 'intro-narration' for you. It's now in your media bin and ready to use. Would you like to place it on the timeline?"
}
```

---

## Key Points for Audio Generation:
- `content_type`: "audio"
- `prompt`: EXACT text script to be spoken
- `voice_settings`: Optional voice configuration (voice_id, language_code, style_prompt, speaking_rate, pitch)
- System returns audio duration (important for timeline sync)
- Agent uses SLEEP to pause and wait for user input
- Do not respond to system generation confirmations
