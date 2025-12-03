# Short Promotional Video

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
  "content": "I'll generate a transparent logo graphic for your brand."
}
```

5. **AGENT - GENERATE**
```json
{
  "type": "generate",
  "content": "Generating a transparent brand logo graphic.",
  "content_type": "logo",
  "prompt": "modern tech icon symbol",
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
  "content": "I'll create a clean end-card background for the finale."
}
```

7. **AGENT - GENERATE**
```json
{
  "type": "generate",
  "content": "Generating a clean, professional brand end-card background for the finale.",
  "content_type": "image",
  "prompt": "16:9 professional brand end-card background, minimal clean design, ample negative space for text overlay, modern tech color palette, subtle texture, elegant and modern, suitable as promotional video end-screen",
  "suggestedName": "promo-brand-endcard"
}
```

**SYSTEM - Generation Result**
```
Successfully generated image: promo-brand-endcard. The image has been added to your media library.
```

8. **AGENT - INFO**
```json
{
  "type": "info",
  "content": "Now I'll analyze all the videos and the end-card to identify the best cinematic moments and text placement opportunities."
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
      "fileName": "promo-brand-endcard",
      "question": "Describe the overall aesthetic, dominant colors with hex codes, background texture/pattern, and optimal text color choices that would contrast well for brand name and CTA text overlays."
    }
  ]
}
```

**SYSTEM - Probe Results**
```
Video 1: Segment A (1.2-3.8s): Close-up detail shot, warm tones (#C4914E), medium lighting, top third clear. Segment B (4.5-7.2s): Wide shot, soft focus, bottom third clear.
Video 2: Segment A (0.8-3.5s): Slow motion, bright lighting (#E8D5B7), center clear. Segment B (5.0-8.0s): Dynamic action, high contrast, upper third clear.
Video 3: Segment A (2.0-5.5s): Lifestyle shot, medium lighting, cool tones (#7FA8C0), middle clear. Segment B (6.2-9.0s): Close detail, clean aesthetic.
promo-brand-endcard: Modern minimal design, blue-gray palette (#546E7A, #ECEFF1), subtle gradient, optimal text: white (#FFFFFF) for high contrast.
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
Successfully generated audio: promo-voiceover (4.8 seconds). The audio has been added to your media library.
```

13. **AGENT - INFO**
```json
{
  "type": "info",
  "content": "Now I'll analyze the voiceover to get precise word-level timestamps for perfect synchronization with the video."
}
```

14. **AGENT - PROBE**
```json
{
  "type": "probe",
  "content": "Analyzing voiceover for word-level timestamps.",
  "files": [
    {
      "fileName": "promo-voiceover",
      "question": "Provide word-level timestamps for the entire audio. For each word, include: the word text, start time in seconds (decimal precision), and end time in seconds (decimal precision)."
    }
  ]
}
```

**SYSTEM - Probe Result**
```
Word-level timestamps:
Discover (0.000-0.612), innovation (0.680-1.425), Experience (1.950-2.621), excellence (2.710-3.452), Transform (3.850-4.380), your (4.420-4.580), world (4.620-4.980)
```

15. **AGENT - INFO**
```json
{
  "type": "info",
  "content": "I've designed the complete visual composition with text overlays, positioning, styling, and transitions that create emotional progression and visual rhythm."
}
```

16. **AGENT - SLEEP**
```json
{
  "type": "sleep",
  "content": "Here's my complete plan for the visual elements:\n\nI'll create a cinematic four-beat structure:\n\n**Beat 1: The Craft** (Video 1, 1.2-3.8s)\n- BlurText 'Discover Innovation' in white, 100px 'Montserrat' bold, center, dark shadow (4px)\n- Text fades out before transition\n\n**Beat 2: The Artistry** (Video 2, 0.8-3.5s)\n- Fade transition (0.5s)\n- SplitText 'Experience Excellence' in white, 90px 'Inter' regular, center, outline (3px), word-by-word\n- Text slides out upward\n\n**Beat 3: The Impact** (Video 3, 2.0-5.5s)\n- Wipe Right transition (0.5s)\n- TypewriterText 'Transform Your World' in white, 110px 'Poppins' bold, center, shadow+outline\n- Text fades out\n\n**Beat 4: The Brand** (promo-brand-endcard)\n- Fade transition (0.5s)\n- Logo 'brand-logo' at top center, 20% width\n- BlurText '[BRAND NAME]' in white, 90px 'Bebas Neue' bold, center\n- BlurText '[CALL TO ACTION]' in white, 50px 'Inter' regular, bottom center\n\nDoes this sound good? Say 'yes' to proceed."
}
```

(Workflow pauses, waits for user confirmation)

--- After user says "yes" ---

17. **AGENT - INFO**
```json
{
  "type": "info",
  "content": "I will now place all visual elements on the timeline."
}
```

18. **AGENT - EDIT**
```json
{
  "type": "edit",
  "content": "1. Add video 'Video 1' at 0.0s on the timeline, trimmed from 1.2s to 3.8s in the source. 2. At 0.5s on the timeline, add BlurText 'Discover Innovation' in white, 100px 'Montserrat' bold, center, dark shadow (4px). 3. At 2.0s on the timeline, fade out the text over 0.3s. 4. Add video 'Video 2' immediately after 'Video 1', trimmed from 0.8s to 3.5s in source. Add 'fade' transition (0.5s) to next on 'Video 1'. 5. At 3.0s on the timeline, add SplitText 'Experience Excellence' in white, 90px 'Inter' regular, center, outline (3px), mode 'words', stagger 0.08. 6. At 5.2s on the timeline, slide out text upward over 0.3s. 7. Add video 'Video 3' immediately after 'Video 2', trimmed from 2.0s to 5.5s in source. Add 'Wipe Right' transition (0.5s) to next on 'Video 2'. 8. At 6.0s on the timeline, add TypewriterText 'Transform Your World' in white, 110px 'Poppins' bold, center, shadow (5px) and outline (2px), typingSpeed 12. 9. At 8.5s on the timeline, fade out text over 0.3s. 10. Add image 'promo-brand-endcard' immediately after 'Video 3'. Add 'fade' transition (0.5s) to next on 'Video 3'. 11. At 9.5s on the timeline, add image 'brand-logo' at top center, 20% width. 12. At 9.5s, add BlurText '[BRAND NAME]' in white, 90px 'Bebas Neue' bold, center. 13. At 9.5s, add BlurText '[CALL TO ACTION]' in white, 50px 'Inter' regular, bottom center."
}
```

**SYSTEM - Tool Response**
```
Edit implemented successfully!
```

19. **AGENT - INFO**
```json
{
  "type": "info",
  "content": "I've determined how to split and synchronize the voiceover across the four beats based on the composition timing and word-level timestamps."
}
```

20. **AGENT - INFO**
```json
{
  "type": "info",
  "content": "I will now place the audio elements on the timeline."
}
```

21. **AGENT - EDIT**
```json
{
  "type": "edit",
  "content": "1. Add audio 'promo-voiceover' at 0.0s on the timeline, trimmed from 0.000s to 1.425s (words 'Discover innovation'), volume 0.8. 2. Add audio 'promo-voiceover' at 2.6s on the timeline, trimmed from 1.950s to 3.452s (words 'Experience excellence'), volume 0.8. 3. Add audio 'promo-voiceover' at 5.7s on the timeline, trimmed from 3.850s to 4.980s (words 'Transform your world'), volume 0.8."
}
```

**SYSTEM - Tool Response**
```
Edit implemented successfully!
```

22. **AGENT - SLEEP**
```json
{
  "type": "sleep",
  "content": "Your promotional video is complete! I've created a four-beat cinematic structure with synchronized voiceover, professional text styling, and a strong branded finale."
}
```

---

