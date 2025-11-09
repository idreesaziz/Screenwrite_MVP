# Question/Information (Atomic Request)

**When to Use:**
- User asks a simple question or requests information
- No action needed, just provide answer

**User Request:** "how long is the video?" or "what's in my media bin?" or "what can you do?"

**Complete Flow:**

1. **CHAT** - Direct answer
   ```json
   {
     "type": "chat",
     "content": "The video 'background.mp4' is 12 seconds long. Would you like to use it in your composition?"
   }
   ```

**→ HALT** (Workflow stops, wait for user's next instruction)

---

## More Examples:

### Example: Media Library Question

**User Request:** "what videos do I have?"

**Complete Flow:**

1. **CHAT**
   ```json
   {
     "type": "chat",
     "content": "You have 3 videos in your media bin: 'background.mp4' (12s), 'intro-clip.mp4' (5s), and 'Ocean Waves 1' (8s). Would you like to use any of these?"
   }
   ```

**→ HALT**

---

### Example: Capability Question

**User Request:** "what can you do?"

**Complete Flow:**

1. **CHAT**
   ```json
   {
     "type": "chat",
     "content": "I can help you create and edit videos! I can search for stock footage, generate images and videos, analyze media content, add text overlays with animations, apply transitions, and much more. What would you like to create?"
   }
   ```

**→ HALT**

---

### Example: Composition Question

**User Request:** "what's currently on the timeline?"

**Complete Flow:**

1. **CHAT**
   ```json
   {
     "type": "chat",
     "content": "Your timeline currently has: 'background.mp4' from 0-12s, and 'Welcome' text from 2-5s. The total duration is 12 seconds. What would you like to add or change?"
   }
   ```

**→ HALT**

---

### Example: Help Question

**User Request:** "how do I add text?"

**Complete Flow:**

1. **CHAT**
   ```json
   {
     "type": "chat",
     "content": "To add text, just tell me what you want it to say, when it should appear, and where you want it positioned. For example: 'Add text that says Welcome at 2 seconds in the center'. Would you like to add some text now?"
   }
   ```

**→ HALT**

---

## Key Points:
- Direct chat response with no other actions
- Provide helpful, concise answers
- End with a prompt to continue the conversation
- No INFO, PROBE, GENERATE, FETCH, or EDIT needed
