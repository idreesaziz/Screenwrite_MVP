# Short Promotional Video

**When to Use:**
- User requests making a promotional/marketing/advertisement video
- Currently in the midst of making a promotional video workflow

**User Request:** "Create a short promotional video" (or similar request)

**Complete Flow:**

1. **INFO**

```json
{
  "type": "info",
  "content": "To create this promotional video, I will need to: 1) Search for high-quality footage, 2) Analyze the footage for cinematic moments and text placement, 3) Design text overlays with compelling messaging, and 4) Structure transitions for smooth pacing. I'll start by searching for stock footage."
}
```

2. **FETCH** - Search for "product detail cinematic"

```json
{
  "type": "fetch",
  "content": "Searching for stock footage: product detail cinematic.",
  "query": "product detail cinematic"
}
```

  → System returns: 3 videos found

3. **INFO**

```json
{
  "type": "info",
  "content": "I found 3 cinematic videos. Now I'll generate the brand assets for the finale, then analyze everything together."
}
```

4. **INFO**

```json
{
  "type": "info",
  "content": "I'll generate a transparent logo graphic for your brand."
}
```

5. **GENERATE** - Logo generation

```json
{
  "type": "generate",
  "content": "Generating a transparent brand logo graphic.",
  "content_type": "logo",
  "prompt": "[brand-aesthetic] icon symbol",
  "suggestedName": "brand-logo"
}
```

6. **INFO**

```json
{
  "type": "info",
  "content": "I'll create a clean end-card background for the finale."
}
```

7. **GENERATE** - Image generation

```json
{
  "type": "generate",
  "content": "Generating a clean, professional brand end-card background for the finale.",
  "content_type": "image",
  "prompt": "16:9 professional brand end-card background, minimal clean design, ample negative space for text overlay, [brand-aesthetic] color palette, subtle texture, elegant and modern, suitable as promotional video end-screen",
  "suggestedName": "promo-brand-endcard"
}
```

8. **INFO**

```json
{
  "type": "info",
  "content": "Now I'll analyze all the videos and the end-card to identify the best cinematic moments and text placement opportunities."
}
```

9. **PROBE** - Analysis of all 3 videos + end-card
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
   → Result (aggregated from all files): 
   
   Video 1 (Video 1): Segment A ([clip-start-time]-[clip-end-time] in source video): Close-up detail shot, [color-description] ([hex-code]), [lighting-type] lighting ([brightness-level]), [placement-area] clear. Segment B ([clip-start-time]-[clip-end-time] in source video): Wide shot, soft focus background, [placement-area] clear.
   
   Video 2 (Video 2): Segment A ([clip-start-time]-[clip-end-time] in source video): Slow motion movement, [lighting-type] lighting ([hex-code]), [placement-area] clear. Segment B ([clip-start-time]-[clip-end-time] in source video): Dynamic action, high contrast ([hex-code] and [hex-code]), [placement-area] clear for text, beautiful visual interest.
   
   Video 3 (Video 3): Segment A ([clip-start-time]-[clip-end-time] in source video): Lifestyle shot, [lighting-type] lighting, [color-description] ([hex-code]), [focus-description] background ([brightness-level]), [placement-area] clear. Segment B ([clip-start-time]-[clip-end-time] in source video): Close detail, clean aesthetic.
   
  End-card (promo-brand-endcard): [aesthetic-description], [color-palette] ([hex-codes]), [texture-description], optimal text colors: [text-color-recommendation] for high contrast.

10. **INFO**

```json
{
  "type": "info",
  "content": "Based on my analysis of all assets, I've selected the most cinematic segments that create a compelling three-beat narrative arc with a strong branded finale. Each segment has clear text placement areas and strong visual interest."
}
```

*[Extended Thinking Context - Model reasons internally about: segment selection criteria, narrative arc progression, timing strategy, emotional flow. Then outputs the INFO above with decisions.]*

11. **INFO**

```json
{
  "type": "info",
  "content": "Now I'll generate a voiceover to narrate the promotional video."
}
```

12. **GENERATE** - Audio generation

```json
{
  "type": "generate",
  "content": "Generating voiceover narration for the promotional video.",
  "content_type": "audio",
  "prompt": "[VOICEOVER-SCRIPT-TEXT]",
  "suggestedName": "promo-voiceover",
  "voice_settings": {
    "voice_id": "Charon",
    "language_code": "en-US",
    "style_prompt": "Speak with confidence and authority, conveying professional credibility and enthusiasm"
  }
}
```

14. **INFO**

```json
{
  "type": "info",
  "content": "Now I'll analyze the voiceover to get precise word-level timestamps for perfect synchronization with the video."
}
```

15. **PROBE** - Analysis of voiceover audio

```json
{
  "type": "probe",
  "content": "Analyzing voiceover for word-level timestamps.",
  "files": [
    {
      "fileName": "promo-voiceover",
      "question": "Provide word-level timestamps for the entire audio. For each word, include: the word text, start time in seconds (decimal precision), and end time in seconds (decimal precision). Format as: word1 (start-end), word2 (start-end), etc."
    }
  ]
}
```
   → Result: Word-level timestamps:
   Word-by-word breakdown with start and end times in seconds (decimal precision to 3 places, e.g., 0.123s, 1.456s)

16. **INFO**

```json
{
  "type": "info",
  "content": "I've designed the complete visual composition with text overlays, positioning, styling, and transitions that create emotional progression and visual rhythm."
}
```

*[Extended Thinking Context - Model reasons internally about: clip selection & sequencing, overlay content strategy, positioning & continuity (center vs top/bottom center), styling choices (colors, sizing 80-120px, shadows vs outlines vs both, font weights), transition strategy (types and durations), timing strategy. Then outputs the INFO above with design decisions.]*

17. **CHAT**

```json
{
  "type": "chat",
  "content": "Here's my complete plan for the visual elements of your promotional video:\n\nI'll create a cinematic four-beat structure that builds emotional engagement through craft, artistry, impact, and a strong brand finish.\n\n**Beat 1: The Craft**\n*   Opens with the detail shot from 'Video 1' ([clip-start-time]s to [clip-end-time]s)\n*   `BlurText` '[BEAT-1-MESSAGE]' in [text-color], 100px 'Montserrat', bold weight, at 'center', with [shadow-color] shadow (4px offset)\n*   *Style justification:* Bold sans-serif with strong shadow for immediate impact. Shadow creates depth against the [background-description]\n*   Text fades out before transition\n\n**Beat 2: The Artistry**\n*   'Fade' transition (0.5s) to 'Video 2' ([clip-start-time]s to [clip-end-time]s)\n*   `SplitText` '[BEAT-2-MESSAGE]' in [text-color], 90px 'Inter', regular weight, at 'center', with [outline-color] outline (3px), word-by-word animation\n*   *Style justification:* Switched to regular weight with outline for contrast from Beat 1. Outline treatment handles [motion-description] better than shadow\n*   Text slides out upward before transition\n\n**Beat 3: The Impact**\n*   'Wipe Right' transition (0.5s) to 'Video 3' ([clip-start-time]s to [clip-end-time]s)\n*   `TypewriterText` '[BEAT-3-MESSAGE]' in [text-color], 110px 'Poppins', bold weight, at 'center', with [shadow-color] shadow (5px offset) and [outline-color] outline (2px)\n*   *Style justification:* Combined shadow + outline for maximum punch on the CTA. Bold weight + larger size (110px) + dual effects create climactic energy\n*   Text fades out before transition\n\n**Beat 4: The Brand**\n*   'Fade' transition (0.5s) to 'promo-brand-endcard'\n*   Place transparent logo 'brand-logo' at 'top center', scaled to 20% of frame width\n*   `BlurText` '[BRAND-NAME]' in [brand-color], 90px 'Bebas Neue', bold weight, at 'center', positioned below logo\n*   `BlurText` '[CTA-MESSAGE]' in [cta-color], 50px 'Inter', regular weight, at 'bottom center'\n*   *Style justification:* Logo graphic at top as visual anchor. Brand name in bold display font (Bebas Neue) centered below logo for immediate recognition. CTA in smaller readable sans-serif at bottom for clear hierarchy: logo → brand name → call-to-action\n*   Holds until end\n\n*Continuity note:* All beats use centered positioning for consistent focus. Styling varies across beats—alternating between shadow-only (Beat 1), outline-only (Beat 2), shadow+outline combo (Beat 3), and clean minimal with logo+text (Beat 4)—creating visual rhythm while maintaining cohesion. Font choices progress from modern sans (Montserrat) → neutral (Inter) → rounded (Poppins) → display (Bebas Neue) for finale. Logo graphic with text creates professional branded finish.\n\nDoes this visual structure work? Say 'yes' to proceed."
}
```

I'll create a cinematic four-beat structure that builds emotional engagement through craft, artistry, impact, and a strong brand finish.

**Beat 1: The Craft**
*   Opens with the detail shot from 'Video 1' ([clip-start-time]s to [clip-end-time]s)
*   `BlurText` '[BEAT-1-MESSAGE]' in [text-color], 100px 'Montserrat', bold weight, at 'center', with [shadow-color] shadow (4px offset)
*   *Style justification:* Bold sans-serif with strong shadow for immediate impact. Shadow creates depth against the [background-description]
*   Text fades out before transition

**Beat 2: The Artistry**
*   'Fade' transition (0.5s) to 'Video 2' ([clip-start-time]s to [clip-end-time]s)
*   `SplitText` '[BEAT-2-MESSAGE]' in [text-color], 90px 'Inter', regular weight, at 'center', with [outline-color] outline (3px), word-by-word animation
*   *Style justification:* Switched to regular weight with outline for contrast from Beat 1. Outline treatment handles [motion-description] better than shadow
*   Text slides out upward before transition

**Beat 3: The Impact**
*   'Wipe Right' transition (0.5s) to 'Video 3' ([clip-start-time]s to [clip-end-time]s)
*   `TypewriterText` '[BEAT-3-MESSAGE]' in [text-color], 110px 'Poppins', bold weight, at 'center', with [shadow-color] shadow (5px offset) and [outline-color] outline (2px)
*   *Style justification:* Combined shadow + outline for maximum punch on the CTA. Bold weight + larger size (110px) + dual effects create climactic energy
*   Text fades out before transition

**Beat 4: The Brand**
*   'Fade' transition (0.5s) to 'promo-brand-endcard'
*   Place transparent logo 'brand-logo' at 'top center', scaled to 20% of frame width
*   `BlurText` '[BRAND-NAME]' in [brand-color], 90px 'Bebas Neue', bold weight, at 'center', positioned below logo
*   `BlurText` '[CTA-MESSAGE]' in [cta-color], 50px 'Inter', regular weight, at 'bottom center'
*   *Style justification:* Logo graphic at top as visual anchor. Brand name in bold display font (Bebas Neue) centered below logo for immediate recognition. CTA in smaller readable sans-serif at bottom for clear hierarchy: logo → brand name → call-to-action
*   Holds until end

*Continuity note:* All beats use centered positioning for consistent focus. Styling varies across beats—alternating between shadow-only (Beat 1), outline-only (Beat 2), shadow+outline combo (Beat 3), and clean minimal with logo+text (Beat 4)—creating visual rhythm while maintaining cohesion. Font choices progress from modern sans (Montserrat) → neutral (Inter) → rounded (Poppins) → display (Bebas Neue) for finale. Logo graphic with text creates professional branded finish.

Does this visual structure work? Say 'yes' to proceed."

    → User: "yes"

18. **INFO**

```json
{
  "type": "info",
  "content": "I will now place all visual elements on the timeline."
}
```

19. **EDIT**

```json
{
  "type": "edit",
  "content": "1. Add video 'Video 1' at 0.0s on the timeline, trimmed to start from [clip-start-time]s in the source video and end at [clip-end-time]s in the source video. 2. At [text-timing]s on the timeline, add BlurText '[BEAT-1-MESSAGE]' in [text-color], 100px 'Montserrat', bold weight, positioned at 'center', with [shadow-color] text shadow (4px offset). 3. At [text-exit-timing]s on the timeline, fade out the '[BEAT-1-MESSAGE]' text over [duration] seconds. 4. Add video 'Video 2' immediately after 'Video 1' on the timeline, trimmed to start from [clip-start-time]s in the source video and end at [clip-end-time]s in the source video. Add a 'fade' transition (0.5s duration) to next on 'Video 1'. 5. At [text-timing]s on the timeline, add SplitText '[BEAT-2-MESSAGE]' in [text-color], 90px 'Inter', regular weight, positioned at 'center', with [outline-color] text outline (3px), mode 'words', stagger [stagger-delay]. 6. At [text-exit-timing]s on the timeline, slide out '[BEAT-2-MESSAGE]' upwards over [duration] seconds. 7. Add video 'Video 3' immediately after 'Video 2' on the timeline, trimmed to start from [clip-start-time]s in the source video and end at [clip-end-time]s in the source video. Add a 'Wipe Right' transition (0.5s duration) to next on 'Video 2'. 8. At [text-timing]s on the timeline, add TypewriterText '[BEAT-3-MESSAGE]' in [text-color], 110px 'Poppins', bold weight, positioned at 'center', with [shadow-color] text shadow (5px offset) and [outline-color] text outline (2px), typingSpeed [typing-speed]. 9. At [text-exit-timing]s on the timeline, fade out '[BEAT-3-MESSAGE]' text over [duration] seconds. 10. Add image 'promo-brand-endcard' immediately after 'Video 3' on the timeline. Add a 'fade' transition (0.5s duration) to next on 'Video 3'. 11. At [text-timing]s on the timeline, add image 'brand-logo' positioned at 'top center', scaled to 20% of frame width. 12. At [text-timing]s on the timeline, add BlurText '[BRAND-NAME]' in [brand-color], 90px 'Bebas Neue', bold weight, positioned at 'center'. 13. At [text-timing]s on the timeline, add BlurText '[CTA-MESSAGE]' in [cta-color], 50px 'Inter', regular weight, positioned at 'bottom center'."
}
```

20. **INFO**

```json
{
  "type": "info",
  "content": "I've determined how to split and synchronize the voiceover across the four beats based on the composition timing and word-level timestamps."
}
```

*[Extended Thinking Context - Model reasons internally about: current composition structure (beat start times and durations), voiceover word timestamps, audio clip placement strategy (which words correspond to which beats, exact startFrom/endAt values), synchronization considerations (alignment with beat starts, decimal precision). Then outputs the INFO above with synchronization decisions.]*

21. **INFO**

```json
{
  "type": "info",
  "content": "I will now place the audio elements on the timeline."
}
```

22. **EDIT**

```json
{
  "type": "edit",
  "content": "Audio placement instructions using precise decimal timestamps from analysis: 1. Add audio from the voiceover file at the start time of Beat 1, trimmed to the exact word range for Beat 1 (using startFrom and endAt with decimal precision). 2. Add audio from the voiceover file at the start time of Beat 2, trimmed to the exact word range for Beat 2. 3. Add audio from the voiceover file at the start time of Beat 3, trimmed to the exact word range for Beat 3. 4. Add audio from the voiceover file at the start time of Beat 4, trimmed to the exact word range for Beat 4. All segments use volume 0.8."
}
```

23. **CHAT**

```json
{
  "type": "chat",
  "content": "Your promotional video is complete! I've created a four-beat cinematic structure with synchronized voiceover, professional text styling, and a strong branded finale."
}
```

**→ DONE**
