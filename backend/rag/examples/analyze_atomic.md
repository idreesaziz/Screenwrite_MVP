# Analyze/Watch Media (Atomic Request)

**When to Use:**
- User requests to analyze, watch, or understand media content
- Simple atomic request with no complex workflow

**User Request:** "watch background.mp4" or "analyze this video" or "what's in this image?"

**Complete Flow:**

1. **INFO** - "I will analyze background.mp4 for you."

2. **PROBE** - Media analysis
   ```json
   {
     "type": "probe",
     "content": "Analyzing background.mp4.",
     "files": [
       {
         "fileName": "background.mp4",
         "question": "Provide a comprehensive analysis: What is happening in this video? Describe key moments with timestamps (in seconds), dominant colors (hex codes), visual composition, any text or objects, mood, and camera movements."
       }
     ]
   }
   ```

   Analysis result: "The video is 12 seconds long and shows a tropical beach at sunset. At 0-4s, calm waves roll onto golden sand (#D4A574) with orange sky (#FF6B35). At 5-8s, camera pans right revealing palm trees (#2E7D32). At 9-12s, sun sets on horizon creating purple hues (#9C27B0). Peaceful, relaxing mood. Static camera with slow pan."

3. **CHAT** - "I've analyzed background.mp4. The video is 12 seconds long and shows a tropical beach at sunset. At 0-4s, calm waves roll onto golden sand with orange sky. At 5-8s, camera pans right revealing palm trees. At 9-12s, sun sets on horizon creating purple hues. The mood is peaceful and relaxing. What would you like to do with this video?"

**→ HALT** (Workflow stops, wait for user's next instruction)

---

## Alternative: Batch Analysis

**User Request:** "watch Video 1 and Video 2"

**Complete Flow:**

1. **INFO** - "I will analyze both videos for you."

2. **PROBE** - Batch analysis
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

3. **CHAT** - "I've analyzed both videos. Video 1 shows... Video 2 shows... Would you like to use either of these in your composition?"

**→ HALT** (Workflow stops, wait for user's next instruction)
