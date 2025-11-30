# Fetch Stock Media (Atomic Request)

**When to Use:**
- User directly requests stock footage search
- Simple atomic request with no complex workflow

**User Request:** "find ocean videos" or "search for mountain footage"

**Complete Flow:**

1. **INFO**

```json
{
  "type": "info",
  "content": "I will search for stock footage of the ocean."
}
```

2. **FETCH** - Stock video search

```json
{
  "type": "fetch",
  "content": "Searching for stock footage of the ocean.",
  "query": "ocean waves"
}
```

   System returns: 3 videos found

3. **CHAT**

```json
{
  "type": "chat",
  "content": "I found 3 ocean videos in the stock library. They are now in your media bin. Would you like me to analyze any of them, or would you like to use them in your composition?"
}
```

**→ HALT** (Workflow stops, wait for user's next instruction)

---

## Key Points:
- Fetch returns videos only (no images in stock)
- Videos are automatically added to media bin
- User can then request analysis or use them directly
