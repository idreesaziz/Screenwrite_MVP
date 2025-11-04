# Coffee Shop Promotional Video

**User Request:** "Create a 15-second promotional video for my coffee shop"

**Complete Flow:**

1. **INFO** - "To create this coffee shop promotional video, I will need to: 1) Search for high-quality coffee footage, 2) Analyze the footage for the best cinematic moments, 3) Generate a custom branding image for your shop, and 4) Design text overlays with warm, inviting messaging. I'll start by searching for stock footage."

2. **FETCH** - Search for "coffee brewing"
   → System returns: 3 videos found

3. **CHAT** - "I found 3 professional coffee videos. Would you like me to analyze them all and select the best segments, or would you prefer to pick specific ones?"
   → User: "you pick"

4. **INFO** - "I'll analyze all three videos to identify the most cinematic coffee moments."

5. **PROBE** Video 1
   ```json
   {
     "type": "probe",
     "content": "Analyzing the first coffee video for usable segments.",
     "fileName": "Coffee Brewing 1",
     "question": "Identify 2-3 distinct, cinematic segments. For each, provide exact start/end timestamps in seconds, describe the action (e.g., 'espresso extraction', 'milk steaming', 'latte art pour'), list dominant colors with hex codes, assess lighting quality (bright/dark/medium), and identify clear areas in upper/middle/lower thirds suitable for text overlays."
   }
   ```
   → Result: Segment A (2-6s): Close-up espresso extraction, rich brown (#3E2723), golden crema (#D4A574), dramatic side lighting (dark background), lower-third clear. Segment B (8-12s): Steam wand in milk, white foam, upper-third clear.

6. **INFO** - "I will now analyze the second coffee video."

7. **PROBE** Video 2
   ```json
   {
     "type": "probe",
     "content": "Analyzing the second coffee video.",
     "fileName": "Coffee Brewing 2",
     "question": "Identify 2-3 distinct, cinematic segments with timestamps, action descriptions, dominant colors (hex codes), lighting assessment (bright/dark/medium), and text overlay suitability."
   }
   ```
   → Result: Segment A (0-5s): Wide shot of coffee bar, warm lighting (#8B6F47), busy composition. Segment B (10-14s): Latte art heart pour, creamy whites (#F5F5DC), rich brown (#4E342E), center clear for text, beautiful contrast, medium-bright lighting.

8. **INFO** - "I will now analyze the third coffee video."

9. **PROBE** Video 3
   ```json
   {
     "type": "probe",
     "content": "Analyzing the third video.",
     "fileName": "Coffee Brewing 3",
     "question": "Identify 2-3 distinct, cinematic segments with timestamps, action descriptions, dominant colors (hex codes), lighting assessment (bright/dark/medium), and text overlay suitability."
   }
   ```
   → Result: Segment A (3-8s): Customer receiving coffee cup in warm café lighting, golden tones (#C9A961), soft bokeh background (medium-light), upper-third clear. Segment B (12-16s): Coffee beans close-up, dark moody aesthetic (#2C1810).

10. **INFO** - "Based on my analysis, I've selected the most cinematic segments: the espresso extraction close-up from Video 1, the latte art pour from Video 2, and the customer moment from Video 3. These create a compelling narrative arc from craft to enjoyment. Now I'll generate a custom branding image for your coffee shop that matches the warm, artisanal aesthetic of the selected footage."

11. **GENERATE** - Image generation
    → content: "Generating a warm, modern coffee shop branding image."
    → content_type: "image"
    → prompt: "16:9 professional coffee shop branding image, centered minimalist coffee cup logo with steam, elegant serif typography 'ARTISAN BREW' below the logo, warm brown and cream color palette (#3E2723, #D4A574, #F5F5DC), subtle texture, clean aesthetic, professional commercial design suitable as full-screen display"
    → suggestedName: "artisan-brew-brand"

12. **CHAT** - "Here's my complete plan for your 15-second coffee shop promotional video:

I'll create a cinematic journey showcasing the artistry of coffee-making, building from the brewing process to the customer experience, with warm, inviting branding.

**Timeline Breakdown (15 seconds):**

*   **0s - 4s: The Craft.** Opens with the dramatic espresso extraction from 'Coffee Brewing 1' (dark browns and golden tones, dark background).
    *   At **0.5s on the timeline**, `BlurText` 'CRAFTED WITH PASSION' appears in bright white (#FFFFFF), 56px bold font, positioned at **bottom center**, with dark brown (#2C1810) text shadow (3px offset) for high contrast against the dark background.
    *   At **3.5s on the timeline**, text fades out over 0.4s.

*   **4s - 9s: The Artistry.** Smooth 'fade' transition to the beautiful latte art pour from 'Coffee Brewing 2' (cream and dark brown, medium-bright lighting).
    *   At **5s on the timeline**, `SplitText` 'EVERY CUP A MASTERPIECE' animates word-by-word in dark brown (#2C1810), 64px bold font, positioned at **center**, with white (#FFFFFF) text outline (3px) for maximum readability against the light foam.
    *   At **8.5s on the timeline**, text slides out to the top over 0.4s.

*   **9s - 13s: The Experience.** 'Wipe Right' transition to customer receiving coffee from 'Coffee Brewing 3' (golden bokeh background, medium-light).
    *   At **9.5s on the timeline**, `TypewriterText` types 'YOUR MORNING RITUAL' in white (#FFFFFF), 52px bold font, positioned at **top center**, with dark brown (#2C1810) text shadow (3px offset) for visibility against the warm bokeh.
    *   At **12.5s on the timeline**, text fades out over 0.3s.

*   **13s - 15s: The Brand.** 'Fade' transition to the 'artisan-brew-brand.png' image (full-screen branding display with light cream background).
    *   At **13.2s on the timeline**, `BlurText` 'VISIT US TODAY' appears in dark brown (#2C1810), 48px bold font, positioned at **bottom center**.
    *   Branding image and text hold until end.

Does this plan capture the artisanal, inviting atmosphere you want for your coffee shop? Say 'yes' to proceed."

    → User: "yes"

13. **INFO** - "Perfect! I'll now create your complete coffee shop promotional video."

14. **EDIT** - "1. Add video 'Coffee Brewing 1' at 0s on the timeline, trimmed to start from 2s in the clip and end at 6s in the clip.
2. At 0.5s on the timeline, add BlurText 'CRAFTED WITH PASSION' in bright white (#FFFFFF), 56px bold font, positioned at bottom center, with dark brown (#2C1810) text shadow (3px offset) for contrast.
3. At 3.5s on the timeline, fade out the 'CRAFTED WITH PASSION' text over 0.4 seconds.
4. Add video 'Coffee Brewing 2' at 4s on the timeline, trimmed to start from 10s in the clip and end at 14s in the clip. Add a 'fade' transition to next on 'Coffee Brewing 1'.
5. At 5s on the timeline, add SplitText 'EVERY CUP A MASTERPIECE' in dark brown (#2C1810), 64px bold font, positioned at center, with white (#FFFFFF) text outline (3px), mode 'word', stagger 0.1.
6. At 8.5s on the timeline, slide out 'EVERY CUP A MASTERPIECE' upwards over 0.4 seconds.
7. Add video 'Coffee Brewing 3' at 9s on the timeline, trimmed to start from 3s in the clip and end at 8s in the clip. Add a 'Wipe Right' transition to next on 'Coffee Brewing 2'.
8. At 9.5s on the timeline, add TypewriterText 'YOUR MORNING RITUAL' in white (#FFFFFF), 52px bold font, positioned at top center, with dark brown (#2C1810) text shadow (3px offset), typingSpeed 12.
9. At 12.5s on the timeline, fade out 'YOUR MORNING RITUAL' text over 0.3 seconds.
10. Add image 'artisan-brew-brand.png' at 13s on the timeline. Add a 'fade' transition to next on 'Coffee Brewing 3'.
11. At 13.2s on the timeline, add BlurText 'VISIT US TODAY' in dark brown (#2C1810), 48px bold font, positioned at bottom center."

**→ DONE**
