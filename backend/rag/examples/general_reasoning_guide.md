# General Reasoning Guide

**When to Use:**
- No specific workflow example matches the request
- Request is unclear, ambiguous, or requires exploration
- Need to think through a complex or creative request step by step

---

**AGENT - INFO**
```json
{
  "type": "info",
  "content": "Let me think through this. I need to understand what assets you have available and what style you're going for."
}
```

---

**AGENT - INFO**
```json
{
  "type": "info",
  "content": "I can see you have 3 videos in your media bin: 'sunset' (12s), 'city' (8s), and 'coffee' (5s). Your timeline is currently empty."
}
```

---

**AGENT - INFO**
```json
{
  "type": "info",
  "content": "To create something with these videos, I could: 1) Analyze them to find the best moments, 2) Create a montage with transitions, or 3) Focus on one video with text overlays. But I need to know what style you want."
}
```

---

**AGENT - SLEEP**
```json
{
  "type": "sleep",
  "content": "What kind of video are you thinking - a fast-paced montage, a calm cinematic piece, or something focused on one clip? This will help me plan the right approach."
}
```

---

**AGENT - INFO**
```json
{
  "type": "info",
  "content": "Great! For a fast-paced montage, I'll need to: 1) Analyze all videos to find dynamic segments, 2) Plan quick cuts with transitions, 3) Add energetic text. Let me start by analyzing the videos."
}
```

---

**AGENT - PROBE**
```json
{
  "type": "probe",
  "content": "Analyzing videos for dynamic moments.",
  "files": [
    {"fileName": "sunset", "question": "Most dynamic segments with timestamps (seconds)."},
    {"fileName": "city", "question": "Most dynamic segments with timestamps (seconds)."},
    {"fileName": "coffee", "question": "Most dynamic segments with timestamps (seconds)."}
  ]
}
```

**SYSTEM - Probe Results** (automatic)
```
sunset: dynamic wave crash at 3-6s
city: fast traffic at 2-5s  
coffee: dramatic pour at 1-3s
```

---

**AGENT - INFO**
```json
{
  "type": "info",
  "content": "Based on the analysis: sunset has a great wave crash at 3-6s, city has fast traffic at 2-5s, coffee has dramatic pour at 1-3s. I'll use these dynamic moments for the montage."
}
```

---

**AGENT - SLEEP**
```json
{
  "type": "sleep",
  "content": "Here's my plan for a fast-paced montage: 0-3s: Coffee pour, 3-6s: City traffic, 6-9s: Beach wave crash. Quick 'wipe' transitions between each. Text: 'ENERGY' at 1s, 'IN MOTION' at 4s, 'UNLEASHED' at 7s. Does this sound good? Say 'yes' to proceed."
}
```

---

**AGENT - INFO**
```json
{
  "type": "info",
  "content": "Perfect! I'll create your fast-paced montage now."
}
```

**AGENT - EDIT**
```json
{
  "type": "edit",
  "content": "1. Add coffee at 0s on the timeline, trimmed from 1s to 3s in the clip. 2. Add city at 3s on the timeline, trimmed from 2s to 5s in the clip, with 'wipe' transition. 3. Add sunset at 6s on the timeline, trimmed from 3s to 6s in the clip, with 'wipe' transition. 4. At 1s on the timeline, add text 'ENERGY' in white, bold, center. 5. At 4s on the timeline, add text 'IN MOTION' in white, bold, center. 6. At 7s on the timeline, add text 'UNLEASHED' in white, bold, center."
}
```

---

**AGENT - SLEEP**
```json
{
  "type": "sleep",
  "content": "Done! Your fast-paced montage is ready with dynamic cuts and energetic text. Want to make any changes?"
}
```
