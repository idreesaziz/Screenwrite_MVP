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
  "content": "I found 3 cinematic videos. Now I'll generate the brand assets for the finale, then analyze everything together."
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
  "content": "I'll create an abstract background with negative space for the finale."
}
```

7. **AGENT - GENERATE**
```json
{
  "type": "generate",
  "content": "Generating an abstract background with negative space for the finale.",
  "content_type": "image",
  "prompt": "16:9 abstract background, clean modern design with ample negative space for text overlay, subtle gradient, modern tech color palette with soft texture, elegant composition",
  "suggestedName": "promo-abstract-bg"
}
```

**SYSTEM - Generation Result**
```
Successfully generated image: promo-abstract-bg. The image has been added to your media library.
```

8. **AGENT - INFO**
```json
{
  "type": "info",
  "content": "Now I'll analyze all the videos and the background to identify the best cinematic moments and text placement opportunities."
}
```

9. **AGENT - PROBE**
```json
{
  "type": "probe",
  "content": "Analyzing all files to identify the best cinematic segments and styling opportunities.",
  "files": [
    {
      "fileName": "Video 1",
      "question": "Identify 2-3 distinct, cinematic segments. For each, provide exact start/end timestamps IN THE SOURCE VIDEO (clip-relative time in seconds), describe the action, list dominant colors with hex codes, assess lighting quality (bright/dark/medium), and identify clear areas in upper/middle/lower thirds suitable for text overlays."
    },
    {
      "fileName": "Video 2",
      "question": "Identify 2-3 distinct, cinematic segments with timestamps IN THE SOURCE VIDEO (clip-relative time), action descriptions, dominant colors (hex codes), lighting assessment (bright/dark/medium), and text overlay suitability."
    },
    {
      "fileName": "Video 3",
      "question": "Identify 2-3 distinct, cinematic segments with timestamps IN THE SOURCE VIDEO (clip-relative time), action descriptions, dominant colors (hex codes), lighting assessment (bright/dark/medium), and text overlay suitability."
    },
    {
      "fileName": "promo-abstract-bg",
      "question": "Describe the overall aesthetic, dominant colors with hex codes, background texture/pattern, and optimal text color choices that would contrast well for text overlays."
    }
  ]
}
```

**SYSTEM - Probe Results**
```
Video 1: Segment A (<START_TIME>-<END_TIME>): Close-up detail shot, warm tones (<HEX_COLOR>), medium lighting, top third clear. Segment B (<START_TIME>-<END_TIME>): Wide shot, soft focus, bottom third clear.
Video 2: Segment A (<START_TIME>-<END_TIME>): Slow motion, bright lighting (<HEX_COLOR>), center clear. Segment B (<START_TIME>-<END_TIME>): Dynamic action, high contrast, upper third clear.
Video 3: Segment A (<START_TIME>-<END_TIME>): Lifestyle shot, medium lighting, cool tones (<HEX_COLOR>), middle clear. Segment B (<START_TIME>-<END_TIME>): Close detail, clean aesthetic.
promo-abstract-bg: Modern minimal design, blue-gray palette (<HEX_COLOR>, <HEX_COLOR>), subtle gradient, optimal text: white (<HEX_COLOR>) for high contrast.
```

10. **AGENT - INFO**
```json
{
  "type": "info",
  "content": "Based on my analysis of all assets, I've selected the most cinematic segments that create a compelling three-beat narrative arc with a strong branded finale. Each segment has clear text placement areas and strong visual interest."
}
```

11. **AGENT - INFO**
```json
{
  "type": "info",
  "content": "Now I'll generate a voiceover to narrate the promotional video."
}
```

12. **AGENT - GENERATE**
```json
{
  "type": "generate",
  "content": "Generating voiceover narration for the promotional video.",
  "content_type": "audio",
  "prompt": "Discover innovation. Experience excellence. Transform your world.",
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
Successfully generated audio: promo-voiceover (<DURATION> seconds). The audio has been added to your media library.

Sentence timestamps: [
  {"word": "Sentence 1", "start": <TIME>, "end": <TIME>},
  {"word": "Sentence 2", "start": <TIME>, "end": <TIME>},
  {"word": "Sentence 3", "start": <TIME>, "end": <TIME>}, ... , 
  {"word": "Sentence N", "start": <TIME>, "end": <TIME>}

]
```

13. **AGENT - INFO**
```json
{
  "type": "info",
  "content": "I've designed the complete visual composition with text overlays synchronized to the voiceover timestamps, creating emotional progression and visual rhythm."
}
```

16. **AGENT - SLEEP**
```json
{
  "type": "sleep",
  "content": "Here's my complete plan for the visual elements:\n\nI'll create a cinematic four-beat structure:\n\n**Beat 1: The Craft** (Video 1, <START>-<END>)\n- BlurText 'Discover Innovation' in white, 96px 'Inter' bold, center, dark shadow (3px)\n- Text fades out before transition\n\n**Beat 2: The Artistry** (Video 2, <START>-<END>)\n- Fade transition (0.5s)\n- SplitText 'Experience Excellence' in white, 96px 'Inter' bold, center, outline (2px), word-by-word\n- Text slides out upward\n\n**Beat 3: The Impact** (Video 3, <START>-<END>)\n- Wipe Right transition (0.5s)\n- TypewriterText 'Transform Your World' in white, 96px 'Inter' bold, center, shadow (3px) + outline (2px)\n- Text fades out\n\n**Beat 4: The Finale** (promo-abstract-bg)\n- Fade transition (0.5s)\n- Logo 'brand-logo' at top center, 200px width\n- BlurText '[BRAND NAME]' in white, 72px 'Inter' bold, center\n- BlurText '[CALL TO ACTION]' in white, 48px 'Inter' bold, bottom center\n\nDoes this sound good? Say 'yes' to proceed."
}
```

(Workflow pauses, waits for user confirmation)

--- After user says "yes" ---

17. **AGENT - INFO**
```json
{
  "type": "info",
  "content": "I will now place all visual and audio elements on the timeline with synchronized voiceover."
}
```

18. **AGENT - EDIT**
```json
{
  "type": "edit",
  "content": "Add video 'Video 1' at 0s on the timeline, trimmed from <SOURCE_START>s to <SOURCE_END>s in the source. At 0.5s on the timeline, add BlurText 'Discover Innovation' in white, 96px 'Inter' bold, center, dark shadow (3px). At 2.5s on the timeline, fade out the text over 0.3s. Add video 'Video 2' immediately after 'Video 1', trimmed from <SOURCE_START>s to <SOURCE_END>s in source. Add 'fade' transition (0.5s) to next on 'Video 1'. At 3.5s on the timeline, add SplitText 'Experience Excellence' in white, 96px 'Inter' bold, center, outline (2px), mode 'words', stagger 0.08. At 5.5s on the timeline, slide out text upward over 0.3s. Add video 'Video 3' immediately after 'Video 2', trimmed from <SOURCE_START>s to <SOURCE_END>s in source. Add 'Wipe Right' transition (0.5s) to next on 'Video 2'. At 6.5s on the timeline, add TypewriterText 'Transform Your World' in white, 96px 'Inter' bold, center, shadow (3px) and outline (2px), typingSpeed 15. At 8.5s on the timeline, fade out text over 0.3s. Add image 'promo-abstract-bg' immediately after 'Video 3'. Add 'fade' transition (0.5s) to next on 'Video 3'. At 9.5s on the timeline, add image 'brand-logo' at top center, 200px width. At 10s, add BlurText '[BRAND NAME]' in white, 72px 'Inter' bold, center. At 10.5s, add BlurText '[CALL TO ACTION]' in white, 48px 'Inter' bold, bottom center. Add audio 'promo-voiceover' at 0s on the timeline, trimmed from <SOURCE_START>s to <SOURCE_END>s (words '<WORD_RANGE>'), volume 1.0. Add audio 'promo-voiceover' at 3s on the timeline, trimmed from <SOURCE_START>s to <SOURCE_END>s (words '<WORD_RANGE>'), volume 1.0. Add audio 'promo-voiceover' at 6s on the timeline, trimmed from <SOURCE_START>s to <SOURCE_END>s (words '<WORD_RANGE>'), volume 1.0."
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

