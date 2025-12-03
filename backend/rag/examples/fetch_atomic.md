# Fetch Stock Media (Atomic Request)

**When to Use:**
- User directly requests stock footage search
- Simple atomic request with no complex workflow

**User Request:** "find ocean videos" or "search for mountain footage"

**Complete Flow:**

1. **AGENT - INFO** (Announce next action)
```json
{
  "type": "info",
  "content": "I will search for stock footage of the ocean."
}
```

2. **AGENT - FETCH** (Search stock library)
```json
{
  "type": "fetch",
  "content": "Searching for stock footage of the ocean.",
  "query": "ocean waves"
}
```

3. **SYSTEM - Fetch Result** (automatic, videos added to media bin)
```
Found 3 ocean videos and added them to your media bin.
```

4. **AGENT - SLEEP** (Pause workflow, wait for user)
```json
{
  "type": "sleep",
  "content": "I found 3 ocean videos in the stock library. They are now in your media bin. Would you like me to analyze any of them, or would you like to use them in your composition?"
}
```

---

## Key Points:
- Fetch returns videos only (no images in stock)
- Videos are automatically added to media bin by system
- Agent uses SLEEP to pause and wait for user direction
- Do not respond to system fetch confirmations - they're tool outputs
