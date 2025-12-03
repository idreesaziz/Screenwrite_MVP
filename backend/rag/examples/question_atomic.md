# Question/Information (Atomic Request)

**When to Use:**
- User asks a simple question or requests information
- No action needed, just provide answer

**User Request:** "how long is the video?" or "what's in my media bin?" or "what can you do?"

**Complete Flow:**

1. **AGENT - SLEEP** (Direct answer, pause for user)
```json
{
  "type": "sleep",
  "content": "The video 'background' is 12 seconds long. Would you like to use it in your composition?"
}
```

---

## More Examples:

### Example: Media Library Question

**User Request:** "what videos do I have?"

1. **AGENT - SLEEP**
```json
{
  "type": "sleep",
  "content": "You have 3 videos in your media bin: 'background' (12s), 'intro-clip' (5s), and 'Ocean Waves 1' (8s). Would you like to use any of these?"
}
```

---

### Example: Capability Question

**User Request:** "what can you do?"

1. **AGENT - SLEEP**
```json
{
  "type": "sleep",
  "content": "I can help you create and edit videos! I can search for stock footage, generate images and videos, analyze media content, add text overlays with animations, apply transitions, and much more. What would you like to create?"
}
```

---

### Example: Composition Question

**User Request:** "what's currently on the timeline?"

1. **AGENT - SLEEP**
```json
{
  "type": "sleep",
  "content": "Your timeline currently has: 'background' from 0-12s, and 'Welcome' text from 2-5s. The total duration is 12 seconds. What would you like to add or change?"
}
```

---

## Key Points:
- Direct SLEEP response with no other actions
- Provide helpful, concise answers
- End with a prompt to continue the conversation
- No INFO, PROBE, GENERATE, FETCH, or EDIT needed
