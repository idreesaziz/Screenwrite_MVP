# Perfume Promotional Video

**User Request:** "I have an image of a perfume and I wanna make a promotional video of it"

**Complete Flow:**

1. **INFO** - "To create a compelling promotional video from your perfume image, I will need to: 1) Analyze your perfume image for composition details, 2) Generate an animated product video using your image as the starting point, 3) Find complementary stock footage for a dynamic opening sequence, and 4) Design text overlays with cinematic timing. I will begin by analyzing your perfume image."

2. **PROBE** - Analyze uploaded perfume image
   ```json
   {
     "type": "probe",
     "content": "Analyzing your perfume image.",
     "fileName": "perfume.png",
     "question": "Describe the perfume bottle's design, color scheme (hex codes), background style, lighting, and overall composition. Identify clear areas suitable for text overlays in upper, middle, and lower thirds."
   }
   ```
   → Result: Elegant glass bottle with gold cap, soft pink liquid (#FFB6C1), white minimal background (#FAFAFA), dramatic side lighting creating highlights, bottle positioned center-left leaving right side clear for text.

3. **INFO** - "Next, I will generate a product showcase video that animates your perfume image with professional camera movements."

4. **GENERATE** - Video generation with seed image
   ```json
   {
     "type": "generate",
     "content": "Generating an 8-second promotional video from your perfume image.",
     "content_type": "video",
     "prompt": "8s cinematic product video, smooth camera orbit around elegant perfume bottle, soft studio lighting with subtle reflections, gentle zoom-in ending on bottle details, professional luxury commercial aesthetic",
     "suggestedName": "perfume-product-shot",
     "seedImageFileName": "perfume.png"
   }
   ```

5. **INFO** - "To create a more dynamic opening sequence, I will also search for perfume spray footage to showcase the product in action."

6. **FETCH** - Search for stock footage
   ```json
   {
     "type": "fetch",
     "content": "I will search for stock footage of perfume being sprayed.",
     "query": "perfume spray"
   }
   ```
   → System returns: 3 videos found

7. **CHAT** - "I found 3 perfume spray videos. Would you like me to analyze them all and select the best match for your promotional video, or would you prefer to pick specific ones?"
   → User: "you pick"

8. **INFO** - "I'll analyze all three videos to identify the most elegant spray footage that matches your perfume's aesthetic. I will begin by analyzing the first video."

9. **PROBE** Video 1
   ```json
   {
     "type": "probe",
     "content": "Analyzing the first perfume spray video.",
     "fileName": "Perfume Spray 1",
     "question": "Describe the spray action, visual style, dominant colors (hex codes), lighting quality (bright/dark/medium), background style, and overall mood. Identify any segments with clear areas for text overlays and note the spray's visual impact."
   }
   ```
   → Result: Elegant slow-motion spray with visible mist particles, soft pink tones (#FFB6C1) matching perfume liquid, white minimal background (#FAFAFA), bright studio lighting, 8s duration, upper-third and left side clear for text, spray creates beautiful diffusion effect.

10. **INFO** - "I will now analyze the second perfume spray video."

11. **PROBE** Video 2
    ```json
    {
      "type": "probe",
      "content": "Analyzing the second perfume spray video.",
      "fileName": "Perfume Spray 2",
      "question": "Describe the spray action, visual style, dominant colors (hex codes), lighting quality, background style, and overall mood. Identify any segments with clear areas for text overlays."
    }
    ```
    → Result: Close-up spray with dramatic backlighting, golden tones (#FFD700), dark background (#1A1A1A), high contrast, more dramatic but doesn't match the soft aesthetic.

12. **INFO** - "I will now analyze the third perfume spray video."

13. **PROBE** Video 3
    ```json
    {
      "type": "probe",
      "content": "Analyzing the third perfume spray video.",
      "fileName": "Perfume Spray 3",
      "question": "Describe the spray action, visual style, dominant colors (hex codes), lighting quality, background style, and overall mood. Identify any segments with clear areas for text overlays."
    }
    ```
    → Result: Multiple spray angles, purple and blue tones (#9370DB, #4169E1), commercial style but color palette doesn't align with perfume's soft pink aesthetic.

14. **INFO** - "Excellent! Video 1 perfectly matches your perfume's aesthetic with its soft pink spray and minimal background. This will create an elegant opening that flows naturally into the generated product video. Now I'll present my complete plan."

15. **CHAT** - "Here is my plan for your perfume promotional video:

I'll create a luxurious 15-second commercial that opens with elegant slow-motion perfume spray (matching your perfume's soft pink tones), then transitions seamlessly to the product showcase video I generated from your image. The entire piece will have a sophisticated, high-end aesthetic.

**Timeline Breakdown (15 seconds):**

*   **0s - 5s: The Spray.** We'll open with the elegant slow-motion perfume spray from 'Perfume Spray 1', showcasing the product in action with beautiful mist diffusion.
    *   At **1s on the timeline**, `BlurText` 'ESSENCE' will appear in the clear upper-third in a refined serif font, soft pink (#FFB6C1) to match the spray and your perfume's aesthetic.
    *   At **4s on the timeline**, this text will fade out over 0.5s as we prepare for the transition.
*   **5s - 15s: The Product.** A smooth 'fade' transition will take us into your 'perfume-product-shot.mp4', the generated video showcasing your actual perfume bottle with cinematic camera movement.
    *   At **6.5s on the timeline**, `TypewriterText` will elegantly reveal 'REDEFINED' in gold (#FFD700) on the right side where your bottle composition leaves clear space, complementing the gold cap.
    *   At **8s on the timeline**, below 'REDEFINED', a `SplitText` element will animate 'LUXURY' word-by-word in white (#FFFFFF) with a subtle pink glow.
    *   At **13.5s on the timeline**, all text elements will fade out over 0.5s, leaving the final product shot to make the lasting impression.

Does this plan capture the luxurious feel you're looking for? Say 'yes' to proceed."

    → User: "yes"

16. **INFO** - "Perfect. I will now create your complete perfume promotional video with both the opening sequence and product showcase."

17. **EDIT** - "1. Add video 'Perfume Spray 1' at 0s on the timeline, trimmed to play for 5 seconds.
2. At 1s on the timeline, add BlurText 'ESSENCE' in soft pink (#FFB6C1), 80px serif font (Georgia), centered in the upper-third.
3. At 4s on the timeline, fade out the 'ESSENCE' text over 0.5 seconds.
4. Add the video perfume-product-shot.mp4 at 5s on the timeline. Add a 'fade' transition to next on 'Perfume Spray 1'.
5. At 6.5s on the timeline, add TypewriterText 'REDEFINED' in gold (#FFD700), 64px serif font (Georgia), positioned in the right third of the frame, vertically centered.
6. At 8s on the timeline, add SplitText 'LUXURY' in white (#FFFFFF), 56px bold font, positioned directly below 'REDEFINED' with 20px spacing, with a soft pink (#FFB6C1) glow shadow, animating word-by-word.
7. At 13.5s on the timeline, fade out both 'REDEFINED' and 'LUXURY' text elements over 0.5 seconds."

**→ DONE**
