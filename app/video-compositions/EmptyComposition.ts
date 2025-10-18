import type { CompositionBlueprint } from './BlueprintTypes';

/**
 * Default boilerplate composition showcasing all transition types
 * Demonstrates the simplified transition system with easing
 */
export const emptyCompositionBlueprint: CompositionBlueprint = [
  // Track 1: Main content demonstrating all transitions
  {
    clips: [
      // 1. Fade transition (0-2s)
      {
        id: "clip-fade",
        startTimeInSeconds: 0,
        endTimeInSeconds: 2,
        element: {
          elements: [
            "div;id:fade-bg;parent:root;width:100%;height:100%;background:#3b82f6;display:flex;justifyContent:center;alignItems:center",
            "h1;id:fade-text;parent:fade-bg;fontSize:72px;fontWeight:bold;color:#ffffff;text:FADE",
          ]
        },
        transitionToNext: {
          type: 'fade',
          durationInSeconds: 0.8
        }
      },
      
      // 2. Slide Left (2-4s)
      {
        id: "clip-slide-left",
        startTimeInSeconds: 2,
        endTimeInSeconds: 4,
        element: {
          elements: [
            "div;id:slide-left-bg;parent:root;width:100%;height:100%;background:#8b5cf6;display:flex;justifyContent:center;alignItems:center",
            "h1;id:slide-left-text;parent:slide-left-bg;fontSize:72px;fontWeight:bold;color:#ffffff;text:SLIDE LEFT",
          ]
        },
        transitionToNext: {
          type: 'slide-left',
          durationInSeconds: 0.6
        }
      },
      
      // 3. Slide Right (4-6s)
      {
        id: "clip-slide-right",
        startTimeInSeconds: 4,
        endTimeInSeconds: 6,
        element: {
          elements: [
            "div;id:slide-right-bg;parent:root;width:100%;height:100%;background:#ec4899;display:flex;justifyContent:center;alignItems:center",
            "h1;id:slide-right-text;parent:slide-right-bg;fontSize:72px;fontWeight:bold;color:#ffffff;text:SLIDE RIGHT",
          ]
        },
        transitionToNext: {
          type: 'slide-right',
          durationInSeconds: 0.6
        }
      },
      
      // 4. Slide Top (6-8s)
      {
        id: "clip-slide-top",
        startTimeInSeconds: 6,
        endTimeInSeconds: 8,
        element: {
          elements: [
            "div;id:slide-top-bg;parent:root;width:100%;height:100%;background:#10b981;display:flex;justifyContent:center;alignItems:center",
            "h1;id:slide-top-text;parent:slide-top-bg;fontSize:72px;fontWeight:bold;color:#ffffff;text:SLIDE TOP",
          ]
        },
        transitionToNext: {
          type: 'slide-top',
          durationInSeconds: 0.6
        }
      },
      
      // 5. Slide Bottom (8-10s)
      {
        id: "clip-slide-bottom",
        startTimeInSeconds: 8,
        endTimeInSeconds: 10,
        element: {
          elements: [
            "div;id:slide-bottom-bg;parent:root;width:100%;height:100%;background:#f59e0b;display:flex;justifyContent:center;alignItems:center",
            "h1;id:slide-bottom-text;parent:slide-bottom-bg;fontSize:72px;fontWeight:bold;color:#ffffff;text:SLIDE BOTTOM",
          ]
        },
        transitionToNext: {
          type: 'slide-bottom',
          durationInSeconds: 0.6
        }
      },
      
      // 6. Wipe Left (10-12s)
      {
        id: "clip-wipe-left",
        startTimeInSeconds: 10,
        endTimeInSeconds: 12,
        element: {
          elements: [
            "div;id:wipe-left-bg;parent:root;width:100%;height:100%;background:#ef4444;display:flex;justifyContent:center;alignItems:center",
            "h1;id:wipe-left-text;parent:wipe-left-bg;fontSize:72px;fontWeight:bold;color:#ffffff;text:WIPE LEFT",
          ]
        },
        transitionToNext: {
          type: 'wipe-left',
          durationInSeconds: 0.7
        }
      },
      
      // 7. Wipe Right (12-14s)
      {
        id: "clip-wipe-right",
        startTimeInSeconds: 12,
        endTimeInSeconds: 14,
        element: {
          elements: [
            "div;id:wipe-right-bg;parent:root;width:100%;height:100%;background:#06b6d4;display:flex;justifyContent:center;alignItems:center",
            "h1;id:wipe-right-text;parent:wipe-right-bg;fontSize:72px;fontWeight:bold;color:#ffffff;text:WIPE RIGHT",
          ]
        },
        transitionToNext: {
          type: 'wipe-right',
          durationInSeconds: 0.7
        }
      },
      
      // 8. Wipe Top-Left (14-16s)
      {
        id: "clip-wipe-top-left",
        startTimeInSeconds: 14,
        endTimeInSeconds: 16,
        element: {
          elements: [
            "div;id:wipe-tl-bg;parent:root;width:100%;height:100%;background:#a855f7;display:flex;justifyContent:center;alignItems:center",
            "h1;id:wipe-tl-text;parent:wipe-tl-bg;fontSize:64px;fontWeight:bold;color:#ffffff;text:WIPE TOP-LEFT",
          ]
        },
        transitionToNext: {
          type: 'wipe-top-left',
          durationInSeconds: 0.7
        }
      },
      
      // 9. Flip Left (16-18s)
      {
        id: "clip-flip-left",
        startTimeInSeconds: 16,
        endTimeInSeconds: 18,
        element: {
          elements: [
            "div;id:flip-left-bg;parent:root;width:100%;height:100%;background:#84cc16;display:flex;justifyContent:center;alignItems:center",
            "h1;id:flip-left-text;parent:flip-left-bg;fontSize:72px;fontWeight:bold;color:#ffffff;text:FLIP LEFT",
          ]
        },
        transitionToNext: {
          type: 'flip-left',
          durationInSeconds: 0.8
        }
      },
      
      // 10. Flip Right (18-20s)
      {
        id: "clip-flip-right",
        startTimeInSeconds: 18,
        endTimeInSeconds: 20,
        element: {
          elements: [
            "div;id:flip-right-bg;parent:root;width:100%;height:100%;background:#f97316;display:flex;justifyContent:center;alignItems:center",
            "h1;id:flip-right-text;parent:flip-right-bg;fontSize:72px;fontWeight:bold;color:#ffffff;text:FLIP RIGHT",
          ]
        },
        transitionToNext: {
          type: 'flip-right',
          durationInSeconds: 0.8
        }
      },
      
      // 11. Clock Wipe (20-22s)
      {
        id: "clip-clock-wipe",
        startTimeInSeconds: 20,
        endTimeInSeconds: 22,
        element: {
          elements: [
            "div;id:clock-bg;parent:root;width:100%;height:100%;background:#dc2626;display:flex;justifyContent:center;alignItems:center",
            "h1;id:clock-text;parent:clock-bg;fontSize:64px;fontWeight:bold;color:#ffffff;text:CLOCK WIPE",
          ]
        },
        transitionToNext: {
          type: 'clock-wipe',
          durationInSeconds: 0.9
        }
      },
      
      // 12. Iris (22-24s)
      {
        id: "clip-iris",
        startTimeInSeconds: 22,
        endTimeInSeconds: 24,
        element: {
          elements: [
            "div;id:iris-bg;parent:root;width:100%;height:100%;background:#0891b2;display:flex;justifyContent:center;alignItems:center",
            "h1;id:iris-text;parent:iris-bg;fontSize:72px;fontWeight:bold;color:#ffffff;text:IRIS",
          ]
        },
        transitionToNext: {
          type: 'iris',
          durationInSeconds: 0.9
        }
      },
      
      // 13. Zoom In (24-26s)
      {
        id: "clip-zoom-in",
        startTimeInSeconds: 24,
        endTimeInSeconds: 26,
        element: {
          elements: [
            "div;id:zoom-in-bg;parent:root;width:100%;height:100%;background:#6366f1;display:flex;justifyContent:center;alignItems:center",
            "h1;id:zoom-in-text;parent:zoom-in-bg;fontSize:72px;fontWeight:bold;color:#ffffff;text:ZOOM IN",
          ]
        },
        transitionToNext: {
          type: 'zoom-in',
          durationInSeconds: 1.0
        }
      },
      
      // 14. Zoom Out (26-28s)
      {
        id: "clip-zoom-out",
        startTimeInSeconds: 26,
        endTimeInSeconds: 28,
        element: {
          elements: [
            "div;id:zoom-out-bg;parent:root;width:100%;height:100%;background:#14b8a6;display:flex;justifyContent:center;alignItems:center",
            "h1;id:zoom-out-text;parent:zoom-out-bg;fontSize:72px;fontWeight:bold;color:#ffffff;text:ZOOM OUT",
          ]
        },
        transitionToNext: {
          type: 'zoom-out',
          durationInSeconds: 1.0
        }
      },
      
      // 15. Blur (28-30s)
      {
        id: "clip-blur",
        startTimeInSeconds: 28,
        endTimeInSeconds: 30,
        element: {
          elements: [
            "div;id:blur-bg;parent:root;width:100%;height:100%;background:#f43f5e;display:flex;justifyContent:center;alignItems:center",
            "h1;id:blur-text;parent:blur-bg;fontSize:72px;fontWeight:bold;color:#ffffff;text:BLUR",
          ]
        },
        transitionToNext: {
          type: 'blur',
          durationInSeconds: 0.8
        }
      },
      
      // 16. Glitch (30-32s)
      {
        id: "clip-glitch",
        startTimeInSeconds: 30,
        endTimeInSeconds: 32,
        element: {
          elements: [
            "div;id:glitch-bg;parent:root;width:100%;height:100%;background:#22c55e;display:flex;justifyContent:center;alignItems:center",
            "h1;id:glitch-text;parent:glitch-bg;fontSize:72px;fontWeight:bold;color:#ffffff;text:GLITCH",
          ]
        },
        transitionToNext: {
          type: 'glitch',
          durationInSeconds: 0.6
        }
      },
      
      // 17. Final clip - Fade out (32-34s)
      {
        id: "clip-finale",
        startTimeInSeconds: 32,
        endTimeInSeconds: 34,
        element: {
          elements: [
            "div;id:finale-bg;parent:root;width:100%;height:100%;background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);display:flex;flexDirection:column;justifyContent:center;alignItems:center;gap:20px",
            "h1;id:finale-title;parent:finale-bg;fontSize:64px;fontWeight:bold;color:#ffffff;text:All Transitions",
            "p;id:finale-subtitle;parent:finale-bg;fontSize:32px;color:#e0e7ff;text:With Custom Effects",
          ]
        }
      }
    ]
  },
  
  // Track 2: Orphaned transition tests - all transitions with both from/to but no adjacent clips
  {
    clips: [
      // 1. Orphaned fade (36-38s)
      {
        id: "orphan-fade",
        startTimeInSeconds: 36,
        endTimeInSeconds: 38,
        element: {
          elements: [
            "div;id:orphan-fade-bg;parent:root;width:100%;height:100%;background:#64748b;display:flex;justifyContent:center;alignItems:center",
            "h2;id:orphan-fade-text;parent:orphan-fade-bg;fontSize:40px;fontWeight:bold;color:#ffffff;text:ORPHAN FADE",
          ]
        },
        transitionFromPrevious: { type: 'fade', durationInSeconds: 0.8 },
        transitionToNext: { type: 'fade', durationInSeconds: 0.8 }
      },
      
      // 2. Orphaned slide-left (40-42s)
      {
        id: "orphan-slide-left",
        startTimeInSeconds: 40,
        endTimeInSeconds: 42,
        element: {
          elements: [
            "div;id:orphan-sl-bg;parent:root;width:100%;height:100%;background:#475569;display:flex;justifyContent:center;alignItems:center",
            "h2;id:orphan-sl-text;parent:orphan-sl-bg;fontSize:36px;fontWeight:bold;color:#ffffff;text:ORPHAN SLIDE-L",
          ]
        },
        transitionFromPrevious: { type: 'slide-left', durationInSeconds: 0.6 },
        transitionToNext: { type: 'slide-left', durationInSeconds: 0.6 }
      },
      
      // 3. Orphaned slide-right (44-46s)
      {
        id: "orphan-slide-right",
        startTimeInSeconds: 44,
        endTimeInSeconds: 46,
        element: {
          elements: [
            "div;id:orphan-sr-bg;parent:root;width:100%;height:100%;background:#64748b;display:flex;justifyContent:center;alignItems:center",
            "h2;id:orphan-sr-text;parent:orphan-sr-bg;fontSize:36px;fontWeight:bold;color:#ffffff;text:ORPHAN SLIDE-R",
          ]
        },
        transitionFromPrevious: { type: 'slide-right', durationInSeconds: 0.6 },
        transitionToNext: { type: 'slide-right', durationInSeconds: 0.6 }
      },
      
      // 4. Orphaned slide-top (48-50s)
      {
        id: "orphan-slide-top",
        startTimeInSeconds: 48,
        endTimeInSeconds: 50,
        element: {
          elements: [
            "div;id:orphan-st-bg;parent:root;width:100%;height:100%;background:#475569;display:flex;justifyContent:center;alignItems:center",
            "h2;id:orphan-st-text;parent:orphan-st-bg;fontSize:36px;fontWeight:bold;color:#ffffff;text:ORPHAN SLIDE-T",
          ]
        },
        transitionFromPrevious: { type: 'slide-top', durationInSeconds: 0.6 },
        transitionToNext: { type: 'slide-top', durationInSeconds: 0.6 }
      },
      
      // 5. Orphaned slide-bottom (52-54s)
      {
        id: "orphan-slide-bottom",
        startTimeInSeconds: 52,
        endTimeInSeconds: 54,
        element: {
          elements: [
            "div;id:orphan-sb-bg;parent:root;width:100%;height:100%;background:#64748b;display:flex;justifyContent:center;alignItems:center",
            "h2;id:orphan-sb-text;parent:orphan-sb-bg;fontSize:36px;fontWeight:bold;color:#ffffff;text:ORPHAN SLIDE-B",
          ]
        },
        transitionFromPrevious: { type: 'slide-bottom', durationInSeconds: 0.6 },
        transitionToNext: { type: 'slide-bottom', durationInSeconds: 0.6 }
      },
      
      // 6. Orphaned wipe-left (56-58s)
      {
        id: "orphan-wipe-left",
        startTimeInSeconds: 56,
        endTimeInSeconds: 58,
        element: {
          elements: [
            "div;id:orphan-wl-bg;parent:root;width:100%;height:100%;background:#475569;display:flex;justifyContent:center;alignItems:center",
            "h2;id:orphan-wl-text;parent:orphan-wl-bg;fontSize:36px;fontWeight:bold;color:#ffffff;text:ORPHAN WIPE-L",
          ]
        },
        transitionFromPrevious: { type: 'wipe-left', durationInSeconds: 0.7 },
        transitionToNext: { type: 'wipe-left', durationInSeconds: 0.7 }
      },
      
      // 7. Orphaned wipe-right (60-62s)
      {
        id: "orphan-wipe-right",
        startTimeInSeconds: 60,
        endTimeInSeconds: 62,
        element: {
          elements: [
            "div;id:orphan-wr-bg;parent:root;width:100%;height:100%;background:#64748b;display:flex;justifyContent:center;alignItems:center",
            "h2;id:orphan-wr-text;parent:orphan-wr-bg;fontSize:36px;fontWeight:bold;color:#ffffff;text:ORPHAN WIPE-R",
          ]
        },
        transitionFromPrevious: { type: 'wipe-right', durationInSeconds: 0.7 },
        transitionToNext: { type: 'wipe-right', durationInSeconds: 0.7 }
      },
      
      // 8. Orphaned wipe-top-left (64-66s)
      {
        id: "orphan-wipe-tl",
        startTimeInSeconds: 64,
        endTimeInSeconds: 66,
        element: {
          elements: [
            "div;id:orphan-wtl-bg;parent:root;width:100%;height:100%;background:#475569;display:flex;justifyContent:center;alignItems:center",
            "h2;id:orphan-wtl-text;parent:orphan-wtl-bg;fontSize:32px;fontWeight:bold;color:#ffffff;text:ORPHAN WIPE-TL",
          ]
        },
        transitionFromPrevious: { type: 'wipe-top-left', durationInSeconds: 0.7 },
        transitionToNext: { type: 'wipe-top-left', durationInSeconds: 0.7 }
      },
      
      // 9. Orphaned flip-left (68-70s)
      {
        id: "orphan-flip-left",
        startTimeInSeconds: 68,
        endTimeInSeconds: 70,
        element: {
          elements: [
            "div;id:orphan-fl-bg;parent:root;width:100%;height:100%;background:#64748b;display:flex;justifyContent:center;alignItems:center",
            "h2;id:orphan-fl-text;parent:orphan-fl-bg;fontSize:36px;fontWeight:bold;color:#ffffff;text:ORPHAN FLIP-L",
          ]
        },
        transitionFromPrevious: { type: 'flip-left', durationInSeconds: 0.8 },
        transitionToNext: { type: 'flip-left', durationInSeconds: 0.8 }
      },
      
      // 10. Orphaned flip-right (72-74s)
      {
        id: "orphan-flip-right",
        startTimeInSeconds: 72,
        endTimeInSeconds: 74,
        element: {
          elements: [
            "div;id:orphan-fr-bg;parent:root;width:100%;height:100%;background:#475569;display:flex;justifyContent:center;alignItems:center",
            "h2;id:orphan-fr-text;parent:orphan-fr-bg;fontSize:36px;fontWeight:bold;color:#ffffff;text:ORPHAN FLIP-R",
          ]
        },
        transitionFromPrevious: { type: 'flip-right', durationInSeconds: 0.8 },
        transitionToNext: { type: 'flip-right', durationInSeconds: 0.8 }
      },
      
      // 11. Orphaned clock-wipe (76-78s)
      {
        id: "orphan-clock",
        startTimeInSeconds: 76,
        endTimeInSeconds: 78,
        element: {
          elements: [
            "div;id:orphan-clock-bg;parent:root;width:100%;height:100%;background:#64748b;display:flex;justifyContent:center;alignItems:center",
            "h2;id:orphan-clock-text;parent:orphan-clock-bg;fontSize:32px;fontWeight:bold;color:#ffffff;text:ORPHAN CLOCK",
          ]
        },
        transitionFromPrevious: { type: 'clock-wipe', durationInSeconds: 0.9 },
        transitionToNext: { type: 'clock-wipe', durationInSeconds: 0.9 }
      },
      
      // 12. Orphaned iris (80-82s)
      {
        id: "orphan-iris",
        startTimeInSeconds: 80,
        endTimeInSeconds: 82,
        element: {
          elements: [
            "div;id:orphan-iris-bg;parent:root;width:100%;height:100%;background:#475569;display:flex;justifyContent:center;alignItems:center",
            "h2;id:orphan-iris-text;parent:orphan-iris-bg;fontSize:36px;fontWeight:bold;color:#ffffff;text:ORPHAN IRIS",
          ]
        },
        transitionFromPrevious: { type: 'iris', durationInSeconds: 0.9 },
        transitionToNext: { type: 'iris', durationInSeconds: 0.9 }
      },
      
      // 13. Orphaned zoom-in (84-86s)
      {
        id: "orphan-zoom-in",
        startTimeInSeconds: 84,
        endTimeInSeconds: 86,
        element: {
          elements: [
            "div;id:orphan-zi-bg;parent:root;width:100%;height:100%;background:#64748b;display:flex;justifyContent:center;alignItems:center",
            "h2;id:orphan-zi-text;parent:orphan-zi-bg;fontSize:36px;fontWeight:bold;color:#ffffff;text:ORPHAN ZOOM-IN",
          ]
        },
        transitionFromPrevious: { type: 'zoom-in', durationInSeconds: 1.0 },
        transitionToNext: { type: 'zoom-in', durationInSeconds: 1.0 }
      },
      
      // 14. Orphaned zoom-out (88-90s)
      {
        id: "orphan-zoom-out",
        startTimeInSeconds: 88,
        endTimeInSeconds: 90,
        element: {
          elements: [
            "div;id:orphan-zo-bg;parent:root;width:100%;height:100%;background:#475569;display:flex;justifyContent:center;alignItems:center",
            "h2;id:orphan-zo-text;parent:orphan-zo-bg;fontSize:36px;fontWeight:bold;color:#ffffff;text:ORPHAN ZOOM-OUT",
          ]
        },
        transitionFromPrevious: { type: 'zoom-out', durationInSeconds: 1.0 },
        transitionToNext: { type: 'zoom-out', durationInSeconds: 1.0 }
      },
      
      // 15. Orphaned blur (92-94s)
      {
        id: "orphan-blur",
        startTimeInSeconds: 92,
        endTimeInSeconds: 94,
        element: {
          elements: [
            "div;id:orphan-blur-bg;parent:root;width:100%;height:100%;background:#64748b;display:flex;justifyContent:center;alignItems:center",
            "h2;id:orphan-blur-text;parent:orphan-blur-bg;fontSize:36px;fontWeight:bold;color:#ffffff;text:ORPHAN BLUR",
          ]
        },
        transitionFromPrevious: { type: 'blur', durationInSeconds: 0.8 },
        transitionToNext: { type: 'blur', durationInSeconds: 0.8 }
      },
      
      // 16. Orphaned glitch (96-98s)
      {
        id: "orphan-glitch",
        startTimeInSeconds: 96,
        endTimeInSeconds: 98,
        element: {
          elements: [
            "div;id:orphan-glitch-bg;parent:root;width:100%;height:100%;background:#475569;display:flex;justifyContent:center;alignItems:center",
            "h2;id:orphan-glitch-text;parent:orphan-glitch-bg;fontSize:36px;fontWeight:bold;color:#ffffff;text:ORPHAN GLITCH",
          ]
        },
        transitionFromPrevious: { type: 'glitch', durationInSeconds: 0.6 },
        transitionToNext: { type: 'glitch', durationInSeconds: 0.6 }
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
