# Generate Voice-Over (Atomic Request)

**When to Use:**
- User directly requests voice-over narration generation
- Simple atomic request with no dependencies or complex workflow
- User provides or implies a text script to be spoken

**User Request:** "generate voice-over narration" or "add voice-over saying 'Welcome to our showcase'" or "create audio narration"

**Complete Flow:**

1. **INFO**

```json
{
  "type": "info",
  "content": "I will generate voice-over narration for you."
}
```

2. **GENERATE** - Audio generation

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

3. **CHAT**

```json
{
  "type": "chat",
  "content": "I've generated 'intro-narration.mp3' for you. It's now in your media bin and ready to use. Would you like to place it on the timeline?"
}
```

**→ HALT** (Workflow stops, wait for user's next instruction)

---

## Key Points for Audio Generation

**Audio (content_type: "audio"):**
- MP3 format using Gemini 2.5 Pro TTS (highest quality, natural conversational delivery)
- `prompt` field contains the EXACT text script to be spoken
- Natural speech with appropriate pacing, intonation, and emotion
- Prompt-based style control via `style_prompt` for nuanced delivery
- Use `voice_settings` to specify voice characteristics (optional):
  - `voice_id`: Gemini voice name (e.g., "Aoede" for warm female, "Charon" for male)
  - `language_code`: Language code (e.g., "en-US", "en-GB", "es-ES")
  - `style_prompt`: Optional delivery style (e.g., "Speak dramatically with urgency", "Whisper quietly [whispering]", "Sound excited and energetic")
  - `speaking_rate`: Speed multiplier (0.25 to 4.0, default 1.0)
  - `pitch`: Voice pitch adjustment (-20.0 to 20.0, default 0.0)

**Style Prompt Examples:**
- "Speak with confidence and authority" - Professional, commanding
- "Speak dramatically with urgency" - Intense, important announcements
- "Whisper quietly [whispering]" - Subtle, intimate tone
- "Sound excited and energetic" - High energy, enthusiastic
- "Speak calmly and soothingly" - Relaxed, comforting
- "Sound mysterious [sarcasm]" - Intriguing, playful
- "[laughing] Speak with joy" - Happy, cheerful delivery
- "[extremely fast] Quick announcement" - Rapid delivery for disclaimers
- "Read with emotion and expression" - Storytelling, narrative

**Gemini TTS Markup Tags (use in style_prompt):**
- `[laughing]` - Add laughter to the delivery
- `[whispering]` - Whisper the text
- `[sarcasm]` - Sarcastic tone
- `[sigh]` - Add a sigh
- `[extremely fast]` - Very fast delivery
- `[short pause]` - Brief pause
- Mix and match: "Start energetically [enthusiastic] then slow down [calm]"

**Gemini 2.5 Pro TTS Voice Options (Recommended):**
- **Female voices** (warm, natural):
  - **Aoede** (default) - Warm, conversational
  - Achernar - Professional, clear
  - Autonoe - Expressive
  - Callirrhoe - Energetic
  - Despina - Calm
  - Erinome - Friendly
  - Gacrux - Authoritative
  - Kore - Versatile
  - Laomedeia - Gentle
  - Leda - Confident
  - Pulcherrima - Elegant
  - Sulafat - Dynamic
  - Vindemiatrix - Professional
  - Zephyr - Light, breezy
  
- **Male voices** (natural, engaging):
  - **Charon** - Professional narrator
  - Achird - Deep, authoritative
  - Algenib - Conversational
  - Algieba - Warm
  - Alnilam - Clear
  - Enceladus - Energetic
  - Fenrir - Strong
  - Iapetus - Calm
  - Orus - Friendly
  - Puck - Playful
  - Rasalgethi - Mature
  - Sadachbia - Smooth
  - Sadaltager - Professional
  - Schedar - Confident
  - Umbriel - Versatile
  - Zubenelgenubi - Dynamic

**Default Behavior:**
- If `voice_settings` is omitted, system uses default voice (Aoede)
- If only `voice_id` provided, system infers appropriate language_code
- If `style_prompt` is omitted, uses natural conversational tone
- Speaking rate and pitch use sensible defaults if not specified

---

## Example Variations

### Promotional Narration (Dramatic)
**User Request:** "create dramatic narration saying 'Discover the future of technology'"

```json
{
  "type": "generate",
  "content": "Generating promotional narration.",
  "content_type": "audio",
  "prompt": "Discover the future of technology. Innovation starts here.",
  "suggestedName": "promo-narration",
  "voice_settings": {
    "voice_id": "Charon",
    "language_code": "en-US",
    "style_prompt": "Speak dramatically with urgency and impact"
  }
}
```

### Instructional Voice-Over (Clear & Calm)
**User Request:** "add voice-over explaining the steps"

```json
{
  "type": "generate",
  "content": "Generating instructional voice-over.",
  "content_type": "audio",
  "prompt": "Step one: Open the application. Step two: Navigate to settings. Step three: Configure your preferences.",
  "suggestedName": "tutorial-steps",
  "voice_settings": {
    "voice_id": "Aoede",
    "language_code": "en-US",
    "style_prompt": "Speak clearly and calmly with helpful tone",
    "speaking_rate": 0.9
  }
}
```

### Storytelling Narration (Mysterious)
**User Request:** "generate narration for a story intro"

```json
{
  "type": "generate",
  "content": "Generating storytelling narration.",
  "content_type": "audio",
  "prompt": "Once upon a time, in a world where imagination knew no bounds, a young dreamer set out on an extraordinary journey.",
  "suggestedName": "story-intro",
  "voice_settings": {
    "voice_id": "Kore",
    "language_code": "en-US",
    "style_prompt": "Sound mysterious [sarcasm] with slow, deliberate pacing",
    "speaking_rate": 0.85,
    "pitch": -2.0
  }
}
```

### Energetic Announcement (Fast & Excited)
**User Request:** "create excited announcement"

```json
{
  "type": "generate",
  "content": "Generating energetic announcement.",
  "content_type": "audio",
  "prompt": "Get ready for the most amazing product launch of the year!",
  "suggestedName": "excited-announcement",
  "voice_settings": {
    "voice_id": "Enceladus",
    "language_code": "en-US",
    "style_prompt": "Sound excited and energetic [enthusiastic] with high energy",
    "speaking_rate": 1.2
  }
}
```

### Whispered Secret (Intimate)
**User Request:** "add whispered narration"

```json
{
  "type": "generate",
  "content": "Generating whispered narration.",
  "content_type": "audio",
  "prompt": "Let me tell you a secret that will change everything.",
  "suggestedName": "whisper-secret",
  "voice_settings": {
    "voice_id": "Laomedeia",
    "language_code": "en-US",
    "style_prompt": "Whisper quietly [whispering] with intimate, close tone"
  }
}
```

---

## Integration with Timeline

After generation, voice-over audio can be:
1. **Placed directly** - "Add intro-narration.mp3 at 0s on the timeline as background audio"
2. **Probed for segments** - "Analyze intro-narration.mp3 to find natural pauses for splitting"
3. **Trimmed and positioned** - "Use intro-narration.mp3 from 2s to 8s, place at 5s on the timeline"
4. **Volume adjusted** - "Add intro-narration.mp3 with 80% volume"

The audio file is treated like any other media asset in the library once generated.
