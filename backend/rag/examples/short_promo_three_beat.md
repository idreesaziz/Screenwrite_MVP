# Short Promotional Video

**Adaptation:** If the user specifies any requirements (style, colors, duration, content, mood, etc.), adapt this workflow accordingly while maintaining the overall structure and flow.

**When to Use:**
- User requests making a promotional/marketing/advertisement video
- Currently in the midst of making a promotional video workflow

**User Request:** "Create a short promotional video"

**Complete Flow:**

1. **AGENT - INFO**
```json
{
  "type": "info",
  "content": "To create this promotional video, I will need to: 1) Search for high-quality footage, 2) Analyze the footage for cinematic moments and text placement, 3) Design text overlays with compelling messaging, and 4) Structure transitions for smooth pacing. I'll start by searching for stock footage."
}
```

2. **AGENT - FETCH**
```json
{
  "type": "fetch",
  "content": "Searching for stock footage: product detail cinematic.",
  "query": "product detail cinematic"
}
```

**SYSTEM - Fetch Result**
```
Found 3 cinematic videos and added them to your media bin.
```

3. **AGENT - INFO**
```json
{
  "type": "info",
  "content": "I found 3 cinematic videos. Now I'll generate a logo for your brand, then analyze the footage."
}
```

4. **AGENT - INFO**
```json
{
  "type": "info",
  "content": "I'll generate a logo graphic for your brand."
}
```

5. **AGENT - GENERATE**
```json
{
  "type": "generate",
  "content": "Generating a transparent logo graphic.",
  "content_type": "logo",
  "prompt": "modern tech icon symbol, graphic only, no text or letters",
  "suggestedName": "brand-logo"
}
```

**SYSTEM - Generation Result**
```
Successfully generated logo: brand-logo. The logo has been added to your media library.
```

6. **AGENT - INFO**
```json
{
  "type": "info",
  "content": "Now I'll analyze all the videos to identify the best cinematic moments and text placement opportunities."
}
```

7. **AGENT - PROBE**
```json
{
  "type": "probe",
  "content": "Analyzing videos for best segments.",
  "files": [
    {
      "fileName": "Video 1",
      "question": "4-5 best moments (up to 6 seconds each): timestamps (seconds), action (1 sentence), best text color for visibility (hex), text placement (top/center/bottom)."
    },
    {
      "fileName": "Video 2",
      "question": "4-5 best moments (up to 6 seconds each): timestamps (seconds), action (1 sentence), best text color for visibility (hex), text placement (top/center/bottom)."
    },
    {
      "fileName": "Video 3",
      "question": "4-5 best moments (up to 6 seconds each): timestamps (seconds), action (1 sentence), best text color for visibility (hex), text placement (top/center/bottom)."
    }
  ]
}
```

**SYSTEM - Probe Results**
```
Video 1: <START>-<END>s <DESCRIPTION> <HEX_COLOR> <PLACEMENT> | <START>-<END>s <DESCRIPTION> <HEX_COLOR> <PLACEMENT> | <START>-<END>s <DESCRIPTION> <HEX_COLOR> <PLACEMENT> | <START>-<END>s <DESCRIPTION> <HEX_COLOR> <PLACEMENT>
Video 2: <START>-<END>s <DESCRIPTION> <HEX_COLOR> <PLACEMENT> | <START>-<END>s <DESCRIPTION> <HEX_COLOR> <PLACEMENT> | <START>-<END>s <DESCRIPTION> <HEX_COLOR> <PLACEMENT> | <START>-<END>s <DESCRIPTION> <HEX_COLOR> <PLACEMENT>
Video 3: <START>-<END>s <DESCRIPTION> <HEX_COLOR> <PLACEMENT> | <START>-<END>s <DESCRIPTION> <HEX_COLOR> <PLACEMENT> | <START>-<END>s <DESCRIPTION> <HEX_COLOR> <PLACEMENT> | <START>-<END>s <DESCRIPTION> <HEX_COLOR> <PLACEMENT>
```

**SELECTION NOTE:** Select sparsely across all videos to maximize variety. Pick 1 best segment per video for each beat - don't reuse the same video multiple times unless necessary.

**VISUAL STRUCTURE NOTE:** First decide the visual structure (number of beats, clip durations, pacing), then generate voiceover with ONE sentence per beat to match. This ensures clean separation.

8. **AGENT - INFO**
```json
{
  "type": "info",
  "content": "Based on the analysis, I've selected 3 video segments for a three-beat structure: Video 1 <START>-<END>s for the opening (<DESCRIPTION>), Video 2 <START>-<END>s for the middle (<DESCRIPTION>), and Video 3 <START>-<END>s for the climax (<DESCRIPTION>). Each segment is approximately 2-3 seconds. I'll also add a 3-second finale beat with your logo."
}
```

9. **AGENT - INFO**
```json
{
  "type": "info",
  "content": "Now I'll generate a voiceover with exactly 3 sentences - one for each visual beat."
}
```

**VOICEOVER WRITING RULES (for reliable sentence detection):**
- Each sentence must have complete grammatical structure: subject + verb + object (NO fragments like "Experience excellence.")
- Each sentence must have exactly ONE period at the end (NO internal periods like "This is more than coffee. This is your moment.")

10. **AGENT - GENERATE**
```json
{
  "type": "generate",
  "content": "Generating voiceover narration with 3 sentences for the 3 visual beats.",
  "content_type": "audio",
  "prompt": "Every great story begins with a single vision. We bring that vision to life with precision and passion. This is where your journey starts.",
  "suggestedName": "promo-voiceover",
  "voice_settings": {
    "voice_id": "Charon",
    "language_code": "en-US",
    "style_prompt": "Speak with confidence and authority, conveying professional credibility and enthusiasm"
  }
}
```

**SYSTEM - Generation Result**
```
Successfully generated audio: promo-voiceover (<TOTAL_DURATION> seconds). The audio has been added to your media library.

Sentence timestamps: [
  {"sentence": "<SENTENCE_1_TEXT>", "start": <S1_START>, "end": <S1_END>},
  {"sentence": "<SENTENCE_2_TEXT>", "start": <S2_START>, "end": <S2_END>},
  {"sentence": "<SENTENCE_3_TEXT>", "start": <S3_START>, "end": <S3_END>}
]
```

11. **AGENT - INFO**
```json
{
  "type": "info",
  "content": "I've designed the visual composition. Each video beat will have its corresponding sentence placed within it."
}
```

12. **AGENT - SLEEP**
```json
{
  "type": "sleep",
  "content": "Here's my plan for your promotional video:\n\n**Beat 1 - Opening:** '<SENTENCE_1_TEXT>' with animated text\n\n**Beat 2 - Middle:** '<SENTENCE_2_TEXT>' with word-by-word reveal\n\n**Beat 3 - Climax:** '<SENTENCE_3_TEXT>' with typewriter effect\n\n**Beat 4 - Finale:** Your brand logo and call-to-action\n\nDoes this sound good? Say 'yes' to proceed."
}
```

(Workflow pauses, waits for user confirmation)

--- After user says "yes" ---

13. **AGENT - INFO**
```json
{
  "type": "info",
  "content": "I will now build the composition - first placing the video clips, then adding text and audio elements."
}
```

**COMPOSITION STRATEGY:** 
1. Place video clips first to establish the visual structure (based on probe analysis)
2. Use voiceover sentence timestamps to place each audio segment at the appropriate position on the timeline
3. Add a small delay (0.3-0.5s) before each audio segment starts within its beat for natural pacing
4. Place text overlays to match audio timing within each beat
5. Text appears slightly before audio starts, fades out as audio ends

14. **AGENT - EDIT**
```json
{
  "type": "edit",
  "content": "Add video 'Video 1' at 0s on the timeline, trimmed from <V1_SOURCE_START>s to <V1_SOURCE_END>s in the source (duration <V1_DURATION>s). Add 'fade' transition (0.3s) to next on 'Video 1'. Add video 'Video 2' immediately after 'Video 1', trimmed from <V2_SOURCE_START>s to <V2_SOURCE_END>s in source (duration <V2_DURATION>s). Add 'wipe-right' transition (0.3s) to next on 'Video 2'. Add video 'Video 3' immediately after 'Video 2', trimmed from <V3_SOURCE_START>s to <V3_SOURCE_END>s in source (duration <V3_DURATION>s). Add 'fade' transition (0.5s) to next on 'Video 3'. Add [best fitting video] immediately after 'Video 3', duration 3.0s, with blur effect (8px) and color tint overlay. Add audio 'promo-voiceover' at 0.3s on the timeline, trimmed from <S1_START>s to <S1_END>s (sentence 1), volume 1.0. Add audio 'promo-voiceover' at <V1_DURATION + 0.3>s on the timeline, trimmed from <S2_START>s to <S2_END>s (sentence 2), volume 1.0. Add audio 'promo-voiceover' at <V1_DURATION + V2_DURATION + 0.3>s on the timeline, trimmed from <S3_START>s to <S3_END>s (sentence 3), volume 1.0. At 0.2s on the timeline, add BlurText '<SENTENCE_1_TEXT>' in white, 96px 'Inter' bold, <PLACEMENT>, dark shadow (3px). Fade out text at <V1_DURATION - 0.3>s over 0.3s. At <V1_DURATION + 0.2>s on the timeline, add SplitText '<SENTENCE_2_TEXT>' in white, 96px 'Inter' bold, <PLACEMENT>, outline (2px), mode 'words', stagger 0.08. Slide out text upward at <V1_DURATION + V2_DURATION - 0.3>s over 0.3s. At <V1_DURATION + V2_DURATION + 0.2>s on the timeline, add TypewriterText '<SENTENCE_3_TEXT>' in white, 96px 'Inter' bold, <PLACEMENT>, shadow (3px) and outline (2px), typingSpeed 15. Fade out text at <V1_DURATION + V2_DURATION + V3_DURATION - 0.3>s over 0.3s. At <FINALE_START + 0.2>s on the timeline, add logo 'brand-logo' at center, 400px width. Add BlurText '[BRAND NAME]' in white, 72px 'Inter' bold, slightly below logo. Add BlurText '[CALL TO ACTION]' in white, 48px 'Inter' bold, bottom center. Fade out the finale video and all finale elements over 0.5s at the end."
}
```

**SYSTEM - Tool Response**
```
Edit implemented successfully!
```

19. **AGENT - SLEEP**
```json
{
  "type": "sleep",
  "content": "Your promotional video is complete! I've created a four-beat cinematic structure with synchronized voiceover, professional text styling, and a strong branded finale."
}
```

---

