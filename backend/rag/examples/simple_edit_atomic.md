# Simple Edit (Atomic Request)

**When to Use:**
- User requests a single, clear edit action with no dependencies
- Simple atomic request that can be executed immediately

**User Request:** "change the text color to red" or "make the font bigger" or "move the image to the left"

**Complete Flow:**

1. **EDIT** - Direct execution
   ```json
   {
     "type": "edit",
     "content": "Change the 'Hello World' text color to red (#FF0000)."
   }
   ```

2. **CHAT** - "Done! I've changed the text color to red (#FF0000). What would you like to do next?"

**→ HALT** (Workflow stops, wait for user's next instruction)

---

## More Examples:

### Example: Font Size Change

**User Request:** "make the title text bigger"

**Complete Flow:**

1. **EDIT**
   ```json
   {
     "type": "edit",
     "content": "Increase the 'Title' text font size to 72px."
   }
   ```

2. **CHAT** - "Done! I've increased the title text to 72px. How does it look?"

**→ HALT**

---

### Example: Position Change

**User Request:** "move the logo to the top right"

**Complete Flow:**

1. **EDIT**
   ```json
   {
     "type": "edit",
    "content": "Move the 'logo' image to the top right corner."
   }
   ```

2. **CHAT** - "Done! I've moved the logo to the top right corner. Anything else?"

**→ HALT**

---

### Example: Duration Change

**User Request:** "make the video clip longer"

**Complete Flow:**

1. **EDIT**
   ```json
   {
     "type": "edit",
    "content": "Extend the 'background' clip to end at 15 seconds on the timeline instead of 10 seconds."
   }
   ```

2. **CHAT** - "Done! I've extended the background video to 15 seconds on the timeline. Is that better?"

**→ HALT**

---

## Key Points:
- Single, clear action with no ambiguity
- No need for planning or confirmation
- Execute immediately and report completion
- Simple changes: color, size, position, duration, etc.
