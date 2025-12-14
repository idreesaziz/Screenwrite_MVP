# Analyze/Watch Media (Atomic Request)

**When to Use:**
- User requests to analyze, watch, or understand media content
- Simple atomic request with no complex workflow

**User Request:** "watch background"

**AGENT - INFO**
```json
{
  "type": "info",
  "content": "I will analyze background for you."
}
```

**AGENT - PROBE**
```json
{
  "type": "probe",
  "content": "Analyzing background.",
  "files": [
    {
      "fileName": "background",
      "question": "Key moments with timestamps (seconds), best text color for visibility (hex), mood, camera movement."
    }
  ]
}
```

**SYSTEM - Analysis Result**
```
The video is 12 seconds long and shows a tropical beach at sunset. At 0-4s, calm waves roll onto golden sand (#D4A574) with orange sky (#FF6B35). At 5-8s, camera pans right revealing palm trees (#2E7D32). At 9-12s, sun sets on horizon creating purple hues (#9C27B0). Peaceful, relaxing mood. Static camera with slow pan.
```

**AGENT - SLEEP**
```json
{
  "type": "sleep",
  "content": "I've analyzed background. The clip is 12 seconds long and shows a tropical beach at sunset. At 0-4s, calm waves roll onto golden sand with orange sky. At 5-8s, camera pans right revealing palm trees. At 9-12s, sun sets on horizon creating purple hues. The mood is peaceful and relaxing. What would you like to do with this video?"
}
```

---

**User Request:** "watch Video 1 and Video 2"

**AGENT - INFO**
```json
{
  "type": "info",
  "content": "I will analyze both videos for you."
}
```

**AGENT - PROBE**
```json
{
  "type": "probe",
  "content": "Analyzing 2 videos.",
  "files": [
    {
      "fileName": "Video 1",
      "question": "Key moments with timestamps (seconds), best text color for visibility (hex)."
    },
    {
      "fileName": "Video 2",
      "question": "Key moments with timestamps (seconds), best text color for visibility (hex)."
    }
  ]
}
```

**SYSTEM - Analysis Results**
```
Video 1 analysis: [detailed analysis with timestamps and colors]
Video 2 analysis: [detailed analysis with timestamps and colors]
```

**AGENT - SLEEP**
```json
{
  "type": "sleep",
  "content": "I've analyzed both videos. Video 1 shows... Video 2 shows... Would you like to use either of these in your composition?"
}
```
