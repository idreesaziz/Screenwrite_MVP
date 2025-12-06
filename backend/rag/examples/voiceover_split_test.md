# Voiceover Splitting Test (Atomic Workflow)

**When to Use:**
- Testing voiceover generation with automatic word-level timestamps
- Validating that Whisper timestamps align correctly with audio
- Demonstrating word-by-word timeline placement

**User Request:** "Generate a voiceover saying 'Welcome to our coffee shop' and show me the word timings"

**AGENT - INFO**
```json
{
  "type": "info",
  "content": "I will generate a voiceover with word-level timestamps and place them on the timeline."
}
```

**AGENT - GENERATE**
```json
{
  "type": "generate",
  "content": "Generating voiceover: 'Welcome to our coffee shop'",
  "content_type": "audio",
  "prompt": "Welcome to our coffee shop",
  "suggestedName": "test-voiceover"
}
```

**SYSTEM - Generation Result**
```
Successfully generated audio: test-voiceover (1.6 seconds). The audio has been added to your media library.

Word timestamps: [
  {"word": "Welcome", "start": 0.0, "end": 0.5},
  {"word": "to", "start": 0.5, "end": 0.65},
  {"word": "our", "start": 0.65, "end": 0.85},
  {"word": "coffee", "start": 0.85, "end": 1.25},
  {"word": "shop", "start": 1.25, "end": 1.6}
]
```

**AGENT - PLACE**
```json
{
  "type": "place",
  "content": "Placing 'Welcome' segment on the timeline",
  "filename": "test-voiceover",
  "track": 1,
  "from": 0.0,
  "to": 0.5,
  "at": 0.0
}
```

**AGENT - PLACE**
```json
{
  "type": "place",
  "content": "Placing 'to' segment on the timeline",
  "filename": "test-voiceover",
  "track": 1,
  "from": 0.5,
  "to": 0.65,
  "at": 0.5
}
```

**AGENT - PLACE**
```json
{
  "type": "place",
  "content": "Placing 'our' segment on the timeline",
  "filename": "test-voiceover",
  "track": 1,
  "from": 0.65,
  "to": 0.85,
  "at": 0.65
}
```

**AGENT - PLACE**
```json
{
  "type": "place",
  "content": "Placing 'coffee' segment on the timeline",
  "filename": "test-voiceover",
  "track": 1,
  "from": 0.85,
  "to": 1.25,
  "at": 0.85
}
```

**AGENT - PLACE**
```json
{
  "type": "place",
  "content": "Placing 'shop' segment on the timeline",
  "filename": "test-voiceover",
  "track": 1,
  "from": 1.25,
  "to": 1.6,
  "at": 1.25
}
```

**AGENT - SLEEP**
```json
{
  "type": "sleep",
  "content": "I've placed all 5 word segments on the timeline:\n\n- 'Welcome' at 0.0s-0.5s\n- 'to' at 0.5s-0.65s\n- 'our' at 0.65s-0.85s\n- 'coffee' at 0.85s-1.25s\n- 'shop' at 1.25s-1.6s\n\nYou can now see the word-by-word spacing on the timeline and verify the timing accuracy."
}
```
