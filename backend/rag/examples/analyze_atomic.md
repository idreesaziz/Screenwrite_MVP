# Analyze/Watch Media (Atomic Request)

**When to Use:**
- User requests to analyze, watch, or understand media content
- Simple atomic request with no complex workflow

**User Request:** "watch background" or "analyze this video" or "what's in this image?"

**Complete Flow:**

1. **AGENT - INFO** (Announce next action)
```json
{
  "type": "info",
  "content": "I will analyze background for you."
}
```

2. **AGENT - PROBE** (Analyze media)
```json
{
  "type": "probe",
  "content": "Analyzing background.",
  "files": [
    {
      "fileName": "background",
      "question": "Provide a comprehensive analysis: What is happening in this video? Describe key moments with timestamps (in seconds), dominant colors (hex codes), visual composition, any text or objects, mood, and camera movements."
    }
  ]
}
```

3. **SYSTEM - Analysis Result** (automatic, returned from probe tool)
```
The video is 12 seconds long and shows a tropical beach at sunset. At 0-4s, calm waves roll onto golden sand (#D4A574) with orange sky (#FF6B35). At 5-8s, camera pans right revealing palm trees (#2E7D32). At 9-12s, sun sets on horizon creating purple hues (#9C27B0). Peaceful, relaxing mood. Static camera with slow pan.
```

4. **AGENT - SLEEP** (Pause workflow, wait for user)
```json
{
  "type": "sleep",
  "content": "I've analyzed background. The clip is 12 seconds long and shows a tropical beach at sunset. At 0-4s, calm waves roll onto golden sand with orange sky. At 5-8s, camera pans right revealing palm trees. At 9-12s, sun sets on horizon creating purple hues. The mood is peaceful and relaxing. What would you like to do with this video?"
}
```

---

## Alternative: Batch Analysis

**User Request:** "watch Video 1 and Video 2"

1. **AGENT - INFO**
```json
{
  "type": "info",
  "content": "I will analyze both videos for you."
}
```

2. **AGENT - PROBE**
```json
{
  "type": "probe",
  "content": "Analyzing 2 videos.",
  "files": [
    {
      "fileName": "Video 1",
      "question": "Describe what's happening in this video with key moments and timestamps."
    },
    {
      "fileName": "Video 2",
      "question": "Describe what's happening in this video with key moments and timestamps."
    }
  ]
}
```

3. **SYSTEM - Analysis Results** (automatic, returned from probe tool)
```
Video 1 analysis: [detailed analysis with timestamps and colors]
Video 2 analysis: [detailed analysis with timestamps and colors]
```

4. **AGENT - SLEEP**
```json
{
  "type": "sleep",
  "content": "I've analyzed both videos. Video 1 shows... Video 2 shows... Would you like to use either of these in your composition?"
}
```

---

## Key Points:
- Use PROBE to analyze media files
- System automatically returns analysis results
- Agent summarizes findings and uses SLEEP to wait for user input
- Do not respond to system analysis results - they're tool outputs, not conversation
