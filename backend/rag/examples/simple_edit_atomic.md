# Simple Edit (Atomic Request)

**When to Use:**
- User requests a single, clear edit action with no dependencies
- Simple atomic request that can be executed immediately

**User Request:** "change the text color to red"

**AGENT - EDIT**
```json
{
  "type": "edit",
  "content": "Change the 'Hello World' text color to red (#FF0000)."
}
```

**SYSTEM - Tool Response**
```
Edit implemented successfully!
```

**AGENT - SLEEP**
```json
{
  "type": "sleep",
  "content": "Done! I've changed the text color to red (#FF0000). What would you like to do next?"
}
```

---

**User Request:** "make the title text bigger"

**AGENT - EDIT**
```json
{
  "type": "edit",
  "content": "Increase the 'Title' text font size to 72px."
}
```

**SYSTEM - Tool Response**
```
Edit implemented successfully!
```

**AGENT - SLEEP**
```json
{
  "type": "sleep",
  "content": "Done! I've increased the title text to 72px. How does it look?"
}
```

---

**User Request:** "move the logo to the top right"

**AGENT - EDIT**
```json
{
  "type": "edit",
  "content": "Move the 'logo' image to the top right corner."
}
```

**SYSTEM - Tool Response**
```
Edit implemented successfully!
```

**AGENT - SLEEP**
```json
{
  "type": "sleep",
  "content": "Done! I've moved the logo to the top right corner. Anything else?"
}
```

---

**User Request:** "make the video clip longer"

**AGENT - EDIT**
```json
{
  "type": "edit",
  "content": "Extend the 'background' clip to end at 15 seconds on the timeline instead of 10 seconds."
}
```

**SYSTEM - Tool Response**
```
Edit implemented successfully!
```

**AGENT - SLEEP**
```json
{
  "type": "sleep",
  "content": "Done! I've extended the background video to 15 seconds on the timeline. Is that better?"
}
```
