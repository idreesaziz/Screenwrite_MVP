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
     "question": "Identify 2-3 distinct, cinematic segments. For each, provide exact start/end timestamps IN THE SOURCE VIDEO (clip-relative time in seconds), describe the action, list dominant colors with hex codes, assess lighting quality (bright/dark/medium), and identify clear areas in upper/middle/lower thirds suitable for text overlays."
   }
   ```
   → Result: Segment A ([clip-start-time]-[clip-end-time] in source video): Close-up detail shot, [color-description] ([hex-code]), [lighting-type] lighting ([brightness-level]), [placement-area] clear. Segment B ([clip-start-time]-[clip-end-time] in source video): Wide shot, soft focus background, [placement-area] clear.

6. **INFO** - "I will now analyze the second video."

7. **PROBE** Video 2
   ```json
   {
     "type": "probe",
     "content": "Analyzing the second video.",
     "fileName": "Video 2",
     "question": "Identify 2-3 distinct, cinematic segments with timestamps IN THE SOURCE VIDEO (clip-relative time), action descriptions, dominant colors (hex codes), lighting assessment (bright/dark/medium), and text overlay suitability."
   }
   ```
   → Result: Segment A ([clip-start-time]-[clip-end-time] in source video): Slow motion movement, [lighting-type] lighting ([hex-code]), [placement-area] clear. Segment B ([clip-start-time]-[clip-end-time] in source video): Dynamic action, high contrast ([hex-code] and [hex-code]), [placement-area] clear for text, beautiful visual interest.

8. **INFO** - "I will now analyze the third video."

9. **PROBE** Video 3
   ```json
   {
     "type": "probe",
     "content": "Analyzing the third video.",
     "fileName": "Video 3",
     "question": "Identify 2-3 distinct, cinematic segments with timestamps IN THE SOURCE VIDEO (clip-relative time), action descriptions, dominant colors (hex codes), lighting assessment (bright/dark/medium), and text overlay suitability."
   }
   ```
   → Result: Segment A ([clip-start-time]-[clip-end-time] in source video): Lifestyle shot, [lighting-type] lighting, [color-description] ([hex-code]), [focus-description] background ([brightness-level]), [placement-area] clear. Segment B ([clip-start-time]-[clip-end-time] in source video): Close detail, clean aesthetic.

10. **INFO** - "Based on my analysis, I've selected the most cinematic segments that create a compelling three-beat narrative arc. These clips have excellent text placement opportunities and visual flow. Now I'll reason through the text styling decisions."

11. **INFO** - "For text styling, I need to consider: 1) Background colors from probe results to determine contrasting text colors, 2) Text length to determine appropriate sizing (short messages = larger text for impact), 3) Available negative space to choose proper anchor positions (top-left, top-center, center, bottom-center, etc.), 4) Motion stability to decide if shadows/outlines are needed for legibility. Let me work through each beat:

**Beat 1 reasoning example:** The probe shows [color-description] background with [brightness-level] lighting. Since the background is [dark/medium/light], I need [contrasting-color] text. The message '[BEAT-1-MESSAGE]' is [X] words, which is [short/medium], so I'll use [size-value] sizing for quick readability. The [placement-area] region is clear and stable, so I'll anchor at [anchor-position] to balance the composition without competing with the main action. Given [lighting-description] lighting, I'll add a [shadow/outline] in [contrast-color] to ensure legibility.

**Beat 2 reasoning example:** Video 2 segment has [contrast-description] with [hex-codes]. The high contrast means text needs strong treatment—I'll use [outline/shadow/panel] approach. Message is [length-description], so [size-reasoning]. The [placement-area] is clear during [motion-description], so [anchor-position] anchor keeps text readable while maintaining visual hierarchy. 

**Beat 3 reasoning example:** The lifestyle shot has [lighting-description] with [color-palette]. This [brightness-level] background works best with [text-color] for maximum contrast. Short, punchy CTA = oversized text ([size-value]) for impact. The [placement-area] provides clean negative space, so [anchor-position] anchor delivers a strong finish without cluttering the hero subject.

I'll now present the complete plan with these styling decisions applied."

12. **CHAT** - "Here's my complete plan for your promotional video:

I'll create a cinematic three-beat structure that builds emotional engagement through craft, artistry, and impact.

**Timeline Breakdown ([total-duration] seconds on the global timeline):**

*   **[timeline-start] - [timeline-end] on timeline: The Craft.** Opens with the detail shot from 'Video 1' ([color-description], [lighting-description]).
    *   Using clip segment from [clip-start-time]s to [clip-end-time]s in the source video.
    *   **Text Reasoning:** The background is [color-description], so I'll use [contrasting-color] for maximum readability. The message is [length-description], so I'll use [size-reasoning] sizing. The [placement-area] has clear negative space, so I'll anchor at [anchor-position] (e.g., 'bottom-center', 'top-left').
    *   At **[timeline-position]s on the global timeline**, `BlurText` '[BEAT-1-MESSAGE]' appears in [text-color], [text-size] [font-family], positioned at [anchor-position], with [shadow-color] text shadow ([shadow-offset] offset) for contrast against [background-description].
    *   At **[timeline-position]s on the global timeline**, text fades out over [duration]s.

*   **[timeline-start] - [timeline-end] on timeline: The Artistry.** Smooth 'fade' transition to the dynamic action from 'Video 2' ([contrast-description], visual interest).
    *   Using clip segment from [clip-start-time]s to [clip-end-time]s in the source video.
    *   **Text Reasoning:** The [contrast-description] background requires [text-treatment] (outline/shadow/panel). Message length is [length-description], so [size-reasoning]. Clear space in [placement-area] means [anchor-position] anchor is optimal.
    *   At **[timeline-position]s on the global timeline**, `SplitText` '[BEAT-2-MESSAGE]' animates word-by-word in [text-color], [text-size] [font-family], positioned at [anchor-position], with [outline-color] text outline ([outline-width]) for maximum readability against [background-description].
    *   At **[timeline-position]s on the global timeline**, text slides out to the top over [duration]s.

*   **[timeline-start] - [timeline-end] on timeline: The Impact.** 'Wipe Right' transition to lifestyle moment from 'Video 3' ([time-of-day], [aesthetic-description]).
    *   Using clip segment from [clip-start-time]s to [clip-end-time]s in the source video.
    *   **Text Reasoning:** [lighting-description] lighting with [color-description] tones means [text-color] will provide best contrast. Short, punchy message = large sizing for impact. [placement-area] is clear, so [anchor-position] anchor creates balanced composition.
    *   At **[timeline-position]s on the global timeline**, `TypewriterText` types '[BEAT-3-MESSAGE]' in [text-color], [text-size] [font-family], positioned at [anchor-position], with [shadow-color] text shadow ([shadow-offset] offset) for visibility against [background-description].
    *   At **[timeline-position]s on the global timeline**, text fades out over [duration]s.

Does this plan capture the right tone and pacing? Say 'yes' to proceed."

    → User: "yes"

13. **INFO** - "Perfect! I'll now create your complete promotional video. I've reasoned through each text placement: Beat 1 uses [anchor-position] because [placement-reasoning], Beat 2 uses [anchor-position] for [composition-reasoning], and Beat 3 uses [anchor-position] to [visual-balance-reasoning]. All colors and sizes are optimized for readability based on background analysis."

14. **EDIT** - "1. Add video 'Video 1' at [timeline-position]s on the global timeline, trimmed to start from [clip-start-time]s in the source video and end at [clip-end-time]s in the source video.
2. At [timeline-position]s on the global timeline, add BlurText '[BEAT-1-MESSAGE]' in [text-color], [text-size] [font-family], positioned at [anchor-position], with [shadow-color] text shadow ([shadow-offset] offset).
3. At [timeline-position]s on the global timeline, fade out the '[BEAT-1-MESSAGE]' text over [duration] seconds.
4. Add video 'Video 2' at [timeline-position]s on the global timeline, trimmed to start from [clip-start-time]s in the source video and end at [clip-end-time]s in the source video. Add a 'fade' transition to next on 'Video 1'.
5. At [timeline-position]s on the global timeline, add SplitText '[BEAT-2-MESSAGE]' in [text-color], [text-size] [font-family], positioned at [anchor-position], with [outline-color] text outline ([outline-width]), mode 'word', stagger [stagger-delay].
6. At [timeline-position]s on the global timeline, slide out '[BEAT-2-MESSAGE]' upwards over [duration] seconds.
7. Add video 'Video 3' at [timeline-position]s on the global timeline, trimmed to start from [clip-start-time]s in the source video and end at [clip-end-time]s in the source video. Add a 'Wipe Right' transition to next on 'Video 2'.
8. At [timeline-position]s on the global timeline, add TypewriterText '[BEAT-3-MESSAGE]' in [text-color], [text-size] [font-family], positioned at [anchor-position], with [shadow-color] text shadow ([shadow-offset] offset), typingSpeed [typing-speed].
9. At [timeline-position]s on the global timeline, fade out '[BEAT-3-MESSAGE]' text over [duration] seconds."

**→ DONE**
