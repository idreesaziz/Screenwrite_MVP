# Short Promotional Video

**User Request:** "Create a short promotional video" (or similar request)

**Complete Flow:**

1. **INFO** - "To create this promotional video, I will need to: 1) Search for high-quality footage, 2) Analyze the footage for cinematic moments and text placement, 3) Design text overlays with compelling messaging, and 4) Structure transitions for smooth pacing. I'll start by searching for stock footage."

2. **FETCH** - Search for "product detail cinematic"
   → System returns: 3 videos found

3. **CHAT** - "I found 3 cinematic videos. Would you like me to analyze them all and select the best segments, or would you prefer to pick specific ones?"
   → User: "you pick"

4. **INFO** - "I'll analyze all three videos to identify the most cinematic moments and text placement opportunities."

5. **PROBE** Video 1
   ```json
   {
     "type": "probe",
     "content": "Analyzing the first video for usable segments.",
     "fileName": "Video 1",
     "question": "Identify 2-3 distinct, cinematic segments. For each, provide exact start/end timestamps in seconds, describe the action, list dominant colors with hex codes, assess lighting quality (bright/dark/medium), and identify clear areas in upper/middle/lower thirds suitable for text overlays."
   }
   ```
   → Result: Segment A ([start-time]-[end-time]): Close-up detail shot, [color-description] ([hex-code]), [lighting-type] lighting ([brightness-level]), [placement-area] clear. Segment B ([start-time]-[end-time]): Wide shot, soft focus background, [placement-area] clear.

6. **INFO** - "I will now analyze the second video."

7. **PROBE** Video 2
   ```json
   {
     "type": "probe",
     "content": "Analyzing the second video.",
     "fileName": "Video 2",
     "question": "Identify 2-3 distinct, cinematic segments with timestamps, action descriptions, dominant colors (hex codes), lighting assessment (bright/dark/medium), and text overlay suitability."
   }
   ```
   → Result: Segment A ([start-time]-[end-time]): Slow motion movement, [lighting-type] lighting ([hex-code]), [placement-area] clear. Segment B ([start-time]-[end-time]): Dynamic action, high contrast ([hex-code] and [hex-code]), [placement-area] clear for text, beautiful visual interest.

8. **INFO** - "I will now analyze the third video."

9. **PROBE** Video 3
   ```json
   {
     "type": "probe",
     "content": "Analyzing the third video.",
     "fileName": "Video 3",
     "question": "Identify 2-3 distinct, cinematic segments with timestamps, action descriptions, dominant colors (hex codes), lighting assessment (bright/dark/medium), and text overlay suitability."
   }
   ```
   → Result: Segment A ([start-time]-[end-time]): Lifestyle shot, [lighting-type] lighting, [color-description] ([hex-code]), [focus-description] background ([brightness-level]), [placement-area] clear. Segment B ([start-time]-[end-time]): Close detail, clean aesthetic.

10. **INFO** - "Based on my analysis, I've selected the most cinematic segments that create a compelling three-beat narrative arc. These clips have excellent text placement opportunities and visual flow. Now I'll reason through the text styling decisions."

11. **INFO** - "For text styling, I need to consider: 1) Background colors from probe results to determine contrasting text colors, 2) Text length to determine appropriate sizing (short messages = larger text for impact), 3) Available negative space to choose proper anchor positions (top-left, top-center, center, bottom-center, etc.), 4) Motion stability to decide if shadows/outlines are needed for legibility. I'll think through each beat's styling requirements based on the probe data."

12. **CHAT** - "Here's my complete plan for your promotional video:

I'll create a cinematic three-beat structure that builds emotional engagement through craft, artistry, and impact.

**Timeline Breakdown ([total-duration] seconds):**

*   **[start-time] - [end-time]: The Craft.** Opens with the detail shot from 'Video 1' ([color-description], [lighting-description]).
    *   **Text Reasoning:** The background is [color-description], so I'll use [contrasting-color] for maximum readability. The message is [length-description], so I'll use [size-reasoning] sizing. The [placement-area] has clear negative space, so I'll anchor at [anchor-position] (e.g., 'bottom-center', 'top-left').
    *   At **[timeline-position] on the timeline**, `BlurText` '[BEAT-1-MESSAGE]' appears in [text-color], [text-size] [font-family], positioned at [anchor-position], with [shadow-color] text shadow ([shadow-offset] offset) for contrast against [background-description].
    *   At **[timeline-position] on the timeline**, text fades out over [duration]s.

*   **[start-time] - [end-time]: The Artistry.** Smooth 'fade' transition to the dynamic action from 'Video 2' ([contrast-description], visual interest).
    *   **Text Reasoning:** The [contrast-description] background requires [text-treatment] (outline/shadow/panel). Message length is [length-description], so [size-reasoning]. Clear space in [placement-area] means [anchor-position] anchor is optimal.
    *   At **[timeline-position] on the timeline**, `SplitText` '[BEAT-2-MESSAGE]' animates word-by-word in [text-color], [text-size] [font-family], positioned at [anchor-position], with [outline-color] text outline ([outline-width]) for maximum readability against [background-description].
    *   At **[timeline-position] on the timeline**, text slides out to the top over [duration]s.

*   **[start-time] - [end-time]: The Impact.** 'Wipe Right' transition to lifestyle moment from 'Video 3' ([time-of-day], [aesthetic-description]).
    *   **Text Reasoning:** [lighting-description] lighting with [color-description] tones means [text-color] will provide best contrast. Short, punchy message = large sizing for impact. [placement-area] is clear, so [anchor-position] anchor creates balanced composition.
    *   At **[timeline-position] on the timeline**, `TypewriterText` types '[BEAT-3-MESSAGE]' in [text-color], [text-size] [font-family], positioned at [anchor-position], with [shadow-color] text shadow ([shadow-offset] offset) for visibility against [background-description].
    *   At **[timeline-position] on the timeline**, text fades out over [duration]s.

Does this plan capture the right tone and pacing? Say 'yes' to proceed."

    → User: "yes"

13. **INFO** - "Perfect! I'll now create your complete promotional video. I've reasoned through each text placement: Beat 1 uses [anchor-position] because [placement-reasoning], Beat 2 uses [anchor-position] for [composition-reasoning], and Beat 3 uses [anchor-position] to [visual-balance-reasoning]. All colors and sizes are optimized for readability based on background analysis."

14. **EDIT** - "1. Add video 'Video 1' at [timeline-position] on the timeline, trimmed to start from [clip-start-time] in the clip and end at [clip-end-time] in the clip.
2. At [timeline-position] on the timeline, add BlurText '[BEAT-1-MESSAGE]' in [text-color], [text-size] [font-family], positioned at [anchor-position], with [shadow-color] text shadow ([shadow-offset] offset).
3. At [timeline-position] on the timeline, fade out the '[BEAT-1-MESSAGE]' text over [duration] seconds.
4. Add video 'Video 2' at [timeline-position] on the timeline, trimmed to start from [clip-start-time] in the clip and end at [clip-end-time] in the clip. Add a 'fade' transition to next on 'Video 1'.
5. At [timeline-position] on the timeline, add SplitText '[BEAT-2-MESSAGE]' in [text-color], [text-size] [font-family], positioned at [anchor-position], with [outline-color] text outline ([outline-width]), mode 'word', stagger [stagger-delay].
6. At [timeline-position] on the timeline, slide out '[BEAT-2-MESSAGE]' upwards over [duration] seconds.
7. Add video 'Video 3' at [timeline-position] on the timeline, trimmed to start from [clip-start-time] in the clip and end at [clip-end-time] in the clip. Add a 'Wipe Right' transition to next on 'Video 2'.
8. At [timeline-position] on the timeline, add TypewriterText '[BEAT-3-MESSAGE]' in [text-color], [text-size] [font-family], positioned at [anchor-position], with [shadow-color] text shadow ([shadow-offset] offset), typingSpeed [typing-speed].
9. At [timeline-position] on the timeline, fade out '[BEAT-3-MESSAGE]' text over [duration] seconds."

**→ DONE**
