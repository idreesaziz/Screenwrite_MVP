# Short Promotional Video

**When to Use:**
- User requests making a promotional/marketing/advertisement video
- Currently in the midst of making a promotional video workflow

**User Request:** "Create a short promotional video" (or similar request)

**Complete Flow:**

1. **INFO** - "To create this promotional video, I will need to: 1) Search for high-quality footage, 2) Analyze the footage for cinematic moments and text placement, 3) Design text overlays with compelling messaging, and 4) Structure transitions for smooth pacing. I'll start by searching for stock footage."

2. **FETCH** - Search for "product detail cinematic"
   → System returns: 3 videos found

3. **CHAT** - "I found 3 cinematic videos. Would you like me to analyze them all and select the best segments, or would you prefer to pick specific ones?"
   → User: "you pick"

4. **INFO** - "I'll analyze all three files to identify the most cinematic moments and text placement opportunities."

5. **PROBE** - Analysis of all 3 files
   ```json
   {
     "type": "probe",
     "content": "Analyzing all 3 files to identify the best cinematic segments.",
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
       }
     ]
   }
   ```
   → Result (aggregated from all 3 files): 
   
   Video 1 (Video 1): Segment A ([clip-start-time]-[clip-end-time] in source video): Close-up detail shot, [color-description] ([hex-code]), [lighting-type] lighting ([brightness-level]), [placement-area] clear. Segment B ([clip-start-time]-[clip-end-time] in source video): Wide shot, soft focus background, [placement-area] clear.
   
   Video 2 (Video 2): Segment A ([clip-start-time]-[clip-end-time] in source video): Slow motion movement, [lighting-type] lighting ([hex-code]), [placement-area] clear. Segment B ([clip-start-time]-[clip-end-time] in source video): Dynamic action, high contrast ([hex-code] and [hex-code]), [placement-area] clear for text, beautiful visual interest.
   
   Video 3 (Video 3): Segment A ([clip-start-time]-[clip-end-time] in source video): Lifestyle shot, [lighting-type] lighting, [color-description] ([hex-code]), [focus-description] background ([brightness-level]), [placement-area] clear. Segment B ([clip-start-time]-[clip-end-time] in source video): Close detail, clean aesthetic.

6. **INFO** - "Based on my analysis, I've selected the most cinematic segments that create a compelling three-beat narrative arc. These clips have excellent text placement opportunities and visual flow. Now I'll generate a clean brand end-card for the finale."

7. **GENERATE** - Image generation
    → content: "Generating a clean, professional brand end-card for the finale."
    → content_type: "image"
    → prompt: "16:9 professional brand end-card, minimal clean design, ample negative space for text overlay, [brand-aesthetic] color palette, subtle texture, elegant and modern, suitable as promotional video end-screen"
    → suggestedName: "promo-brand-endcard"

8. **INFO** - "Now I'll reason through the text styling decisions."

9. **INFO** - "I've analyzed the segments and designed the complete composition with text overlays, positioning, styling, and transitions. Let me present the plan."

10. **CHAT** - "*[Internal Reasoning - Not Output to User]:*
*Before presenting the plan, I reason through these dimensions:*

1. **Clip Selection & Sequencing:** Which segments best represent each beat? What trim ranges maximize visual interest while staying concise?
2. **Overlay Content Strategy:** What messaging creates emotional progression? Short, punchy messages = opportunity for bold, large sizing that commands attention.
3. **Overlay Positioning & Continuity:** Based on probe data (colors, brightness, clear regions), which anchor positions provide best legibility? Default to 'center' for maximum impact—it's the most powerful position, commanding full attention. Use 'top center' or 'bottom center' only when the center region has critical action or visual clutter. How does positioning guide the viewer's eye through the narrative?
4. **Overlay Styling:** What text colors contrast with each background? For promotional videos, favor large, bold sizing (80px-120px range) that fills the frame with confidence. Mix and match styling treatments across beats for visual variety—use shadows on some beats, outlines on others, or combine both. Vary font weights (bold vs regular) to create rhythm. What shadows/outlines ensure legibility against busy backgrounds?
5. **Transition Strategy:** Which transition types ('fade', 'Wipe Right', etc.) and durations (0.5s, 1.0s) match the emotional tone of each beat shift?
6. **Timing Strategy:** When should text appear/exit relative to clip action to maximize impact without overwhelming the visual?

*[Output to User - Polished Plan]:*

Here's my complete plan for your promotional video:

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
*   'Fade' transition (0.5s) to 'promo-brand-endcard.png'
*   `BlurText` '[BRAND-NAME]' in [brand-color], 120px 'Bebas Neue', bold weight, at 'center'
*   `BlurText` '[CTA-MESSAGE]' in [cta-color], 60px 'Inter', regular weight, at 'bottom center'
*   *Style justification:* Condensed display font (Bebas Neue) for massive brand presence. Minimal effects on clean background. CTA uses readable sans-serif at smaller size for hierarchy
*   Holds until end

*Continuity note:* All beats use centered positioning for consistent focus. Styling varies across beats—alternating between shadow-only (Beat 1), outline-only (Beat 2), shadow+outline combo (Beat 3), and clean minimal (Beat 4)—creating visual rhythm while maintaining cohesion. Font choices progress from modern sans (Montserrat) → neutral (Inter) → rounded (Poppins) → display (Bebas Neue).

Does this work? Say 'yes' to proceed."

    → User: "yes"

11. **EDIT** - "1. Add video 'Video 1' at 0s on the timeline, trimmed to start from [clip-start-time]s in the source video and end at [clip-end-time]s in the source video.
2. At [text-timing]s on the timeline, add BlurText '[BEAT-1-MESSAGE]' in [text-color], 100px 'Montserrat', bold weight, positioned at 'center', with [shadow-color] text shadow (4px offset).
3. At [text-exit-timing]s on the timeline, fade out the '[BEAT-1-MESSAGE]' text over [duration] seconds.
4. Add video 'Video 2' immediately after 'Video 1' on the timeline, trimmed to start from [clip-start-time]s in the source video and end at [clip-end-time]s in the source video. Add a 'fade' transition (0.5s duration) to next on 'Video 1'.
5. At [text-timing]s on the timeline, add SplitText '[BEAT-2-MESSAGE]' in [text-color], 90px 'Inter', regular weight, positioned at 'center', with [outline-color] text outline (3px), mode 'words', stagger [stagger-delay].
6. At [text-exit-timing]s on the timeline, slide out '[BEAT-2-MESSAGE]' upwards over [duration] seconds.
7. Add video 'Video 3' immediately after 'Video 2' on the timeline, trimmed to start from [clip-start-time]s in the source video and end at [clip-end-time]s in the source video. Add a 'Wipe Right' transition (0.5s duration) to next on 'Video 2'.
8. At [text-timing]s on the timeline, add TypewriterText '[BEAT-3-MESSAGE]' in [text-color], 110px 'Poppins', bold weight, positioned at 'center', with [shadow-color] text shadow (5px offset) and [outline-color] text outline (2px), typingSpeed [typing-speed].
9. At [text-exit-timing]s on the timeline, fade out '[BEAT-3-MESSAGE]' text over [duration] seconds.
10. Add image 'promo-brand-endcard.png' immediately after 'Video 3' on the timeline. Add a 'fade' transition (0.5s duration) to next on 'Video 3'.
11. At [text-timing]s on the timeline, add BlurText '[BRAND-NAME]' in [brand-color], 120px 'Bebas Neue', bold weight, positioned at 'center'.
12. At [text-timing]s on the timeline, add BlurText '[CTA-MESSAGE]' in [cta-color], 60px 'Inter', regular weight, positioned at 'bottom center'."

**→ DONE**
