import type { CompositionBlueprint } from './BlueprintTypes';

/**
 * Test composition showcasing all custom text animation components
 */
export const emptyCompositionBlueprint: CompositionBlueprint = [
  // Track 1: Background layer
  {
    clips: [
      {
        id: "background",
        startTimeInSeconds: 0,
        endTimeInSeconds: 30,
        element: {
          elements: [
            "div;id:bg;parent:root;width:100%;height:100%;background:linear-gradient(135deg, #1e3a8a 0%, #7c3aed 100%)"
          ]
        }
      }
    ]
  },
  // Track 2: Text animations showcase
  {
    clips: [
      // 1. SplitText (0-5s) - Character by character
      {
        id: "split-char",
        startTimeInSeconds: 0,
        endTimeInSeconds: 5,
        element: {
          elements: [
            "div;id:split-char-container;position:absolute;top:15%;left:50%;transform:translateX(-50%);width:80%;textAlign:center",
            "SplitText;id:split-char-text;parent:split-char-container;text:SPLIT TEXT - CHARACTER;fontSize:56px;fontWeight:bold;color:#ffffff;animateBy:char;direction:up;delay:0.5;duration:1"
          ]
        }
      },
      // 2. SplitText (5-10s) - Word by word
      {
        id: "split-word",
        startTimeInSeconds: 5,
        endTimeInSeconds: 10,
        element: {
          elements: [
            "div;id:split-word-container;position:absolute;top:15%;left:50%;transform:translateX(-50%);width:80%;textAlign:center",
            "SplitText;id:split-word-text;parent:split-word-container;text:SPLIT TEXT - WORD BY WORD;fontSize:56px;fontWeight:bold;color:#fbbf24;animateBy:word;direction:left;delay:0.3;duration:0.8"
          ]
        },
        transitionFromPrevious: { type: 'fade', durationInSeconds: 0.5 }
      },
      // 3. BlurText (10-15s)
      {
        id: "blur-text",
        startTimeInSeconds: 10,
        endTimeInSeconds: 15,
        element: {
          elements: [
            "div;id:blur-container;position:absolute;top:15%;left:50%;transform:translateX(-50%);width:80%;textAlign:center",
            "BlurText;id:blur-text-comp;parent:blur-container;text:BLUR TEXT ANIMATION;fontSize:64px;fontWeight:bold;color:#34d399;animateBy:word;direction:down;delay:0.2;duration:1.2"
          ]
        },
        transitionFromPrevious: { type: 'fade', durationInSeconds: 0.5 }
      },
      // 4. TypewriterText (15-20s)
      {
        id: "typewriter",
        startTimeInSeconds: 15,
        endTimeInSeconds: 20,
        element: {
          elements: [
            "div;id:typewriter-container;position:absolute;top:15%;left:50%;transform:translateX(-50%);width:80%;textAlign:center",
            "TypewriterText;id:typewriter-text;parent:typewriter-container;text:Typewriter Effect With Cursor...;fontSize:48px;fontWeight:500;color:#60a5fa;typingSpeed:10;initialDelay:0.3;showCursor:true;cursorCharacter:_;cursorBlinkSpeed:0.5"
          ]
        },
        transitionFromPrevious: { type: 'fade', durationInSeconds: 0.5 }
      }
    ]
  },
  // Track 3: Labels/descriptions
  {
    clips: [
      {
        id: "label-split-char",
        startTimeInSeconds: 0,
        endTimeInSeconds: 5,
        element: {
          elements: [
            "div;id:label1-container;position:absolute;bottom:20%;left:50%;transform:translateX(-50%);textAlign:center",
            "p;id:label1;parent:label1-container;fontSize:20px;color:rgba(255,255,255,0.7);text:animateBy: char | direction: up"
          ]
        }
      },
      {
        id: "label-split-word",
        startTimeInSeconds: 5,
        endTimeInSeconds: 10,
        element: {
          elements: [
            "div;id:label2-container;position:absolute;bottom:20%;left:50%;transform:translateX(-50%);textAlign:center",
            "p;id:label2;parent:label2-container;fontSize:20px;color:rgba(255,255,255,0.7);text:animateBy: word | direction: left"
          ]
        }
      },
      {
        id: "label-blur",
        startTimeInSeconds: 10,
        endTimeInSeconds: 15,
        element: {
          elements: [
            "div;id:label3-container;position:absolute;bottom:20%;left:50%;transform:translateX(-50%);textAlign:center",
            "p;id:label3;parent:label3-container;fontSize:20px;color:rgba(255,255,255,0.7);text:Blur-to-focus animation with word-by-word reveal"
          ]
        }
      },
      {
        id: "label-typewriter",
        startTimeInSeconds: 15,
        endTimeInSeconds: 20,
        element: {
          elements: [
            "div;id:label4-container;position:absolute;bottom:20%;left:50%;transform:translateX(-50%);textAlign:center",
            "p;id:label4;parent:label4-container;fontSize:20px;color:rgba(255,255,255,0.7);text:Classic typewriter with blinking cursor"
          ]
        }
      },
      {
        id: "label-decrypted",
        startTimeInSeconds: 20,
        endTimeInSeconds: 25,
        element: {
          elements: [
            "div;id:label5-container;position:absolute;bottom:20%;left:50%;transform:translateX(-50%);textAlign:center",
            "p;id:label5;parent:label5-container;fontSize:20px;color:rgba(255,255,255,0.7);text:Hacker-style character randomization reveal"
          ]
        }
      },
      {
        id: "label-glitch",
        startTimeInSeconds: 25,
        endTimeInSeconds: 30,
        element: {
          elements: [
            "div;id:label6-container;position:absolute;bottom:20%;left:50%;transform:translateX(-50%);textAlign:center",
            "p;id:label6;parent:label6-container;fontSize:20px;color:rgba(255,255,255,0.7);text:Digital glitch effect with RGB shadows"
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
