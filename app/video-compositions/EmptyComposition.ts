import type { CompositionBlueprint } from './BlueprintTypes';

/**
 * Default boilerplate composition with sample content for testing
 * This serves as the starting point showing users what's possible
 * Includes text elements and transitions for demonstration
 */
export const emptyCompositionBlueprint: CompositionBlueprint = [
  // Track 1: Background gradient
  {
    clips: [
      {
        id: "background",
        startTimeInSeconds: 0,
        endTimeInSeconds: 6,
        element: {
          elements: [
            "div;id:bg-gradient;parent:root;width:100%;height:100%;background:linear-gradient(135deg, #1e293b 0%, #0f172a 100%)",
          ]
        }
      }
    ]
  },
  // Track 2: Subtitle text throughout
  {
    clips: [
      {
        id: "subtitle",
        startTimeInSeconds: 0,
        endTimeInSeconds: 6,
        element: {
          elements: [
            "div;id:subtitle-container;parent:root;display:flex;justifyContent:center;alignItems:flex-end;width:100%;height:100%;paddingBottom:80px",
            "p;id:subtitle-text;parent:subtitle-container;fontSize:24px;color:#d1d5db;text:AI-powered video editing made simple",
          ]
        }
      }
    ]
  },
  // Track 3: Main title texts with fade transition
  {
    clips: [
      {
        id: "welcome-title",
        startTimeInSeconds: 0,
        endTimeInSeconds: 3,
        element: {
          elements: [
            "div;id:title-container;parent:root;display:flex;flexDirection:column;justifyContent:center;alignItems:center;width:100%;height:100%",
            "h1;id:main-title;parent:title-container;fontSize:64px;fontWeight:bold;color:#ffffff;text:Welcome to Screenwrite",
          ]
        },
        transitionToNext: {
          type: 'fade',
          durationInSeconds: 0.5
        }
      },
      {
        id: "create-title",
        startTimeInSeconds: 3,
        endTimeInSeconds: 6,
        element: {
          elements: [
            "div;id:title-container-2;parent:root;display:flex;flexDirection:column;justifyContent:center;alignItems:center;width:100%;height:100%",
            "h1;id:create-text;parent:title-container-2;fontSize:56px;fontWeight:bold;color:#60a5fa;text:Start creating your video",
          ]
        }
      }
    ]
  }
];

/**
 * Ensure composition has minimum required tracks
 * Automatically expands to accommodate content without losing existing data
 */
export function ensureMinimumTracks(blueprint: CompositionBlueprint, minTracks: number = 4): CompositionBlueprint {
  const result = [...blueprint];
  
  // Add empty tracks if we don't have enough
  while (result.length < minTracks) {
    result.push({ clips: [] });
  }
  
  return result;
}
