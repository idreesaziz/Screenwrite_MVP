# Fetch Stock Media (Atomic Request)

**When to Use:**
- User directly requests stock footage search
- Simple atomic request with no complex workflow

**User Request:** "find ocean videos"

**AGENT - INFO**
```json
{
  "type": "info",
  "content": "I will search for stock footage of the ocean."
}
```

**AGENT - FETCH**
```json
{
  "type": "fetch",
  "content": "Searching for stock footage of the ocean.",
  "query": "ocean waves"
}
```

**SYSTEM - Fetch Result**
```
Found 3 ocean videos and added them to your media bin.
```

**AGENT - SLEEP**
```json
{
  "type": "sleep",
  "content": "I found 3 ocean videos in the stock library. They are now in your media bin. Would you like me to analyze any of them, or would you like to use them in your composition?"
}
```
