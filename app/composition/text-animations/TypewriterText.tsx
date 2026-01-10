import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';

export interface TypewriterTextProps {
  text: string | string[];  // Single text or array for multiple texts
  typingSpeed?: number;     // Characters per second
  initialDelay?: number;    // Delay before typing starts (seconds)
  pauseDuration?: number;   // Pause between texts when looping (seconds)
  deletingSpeed?: number;   // Characters per second when deleting
  loop?: boolean;           // Loop through multiple texts
  showCursor?: boolean;     // Show blinking cursor
  cursorCharacter?: string; // Cursor character (default '|')
  cursorBlinkSpeed?: number; // Cursor blinks per second
  style?: React.CSSProperties;
  className?: string;
}

/**
 * TypewriterText - Typewriter effect with optional cursor
 * Types out text character by character, can loop through multiple texts
 */
export const TypewriterText: React.FC<TypewriterTextProps> = ({
  text,
  typingSpeed = 10,        // 10 chars per second
  initialDelay = 0,
  pauseDuration = 1,       // 1 second pause
  deletingSpeed = 20,      // 20 chars per second when deleting
  loop = false,
  showCursor = true,
  cursorCharacter = '|',
  cursorBlinkSpeed = 2,    // 2 blinks per second
  style = {},
  className = '',
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  // Convert to array for consistent handling
  const textArray = Array.isArray(text) ? text : [text];
  const shouldLoop = loop && textArray.length > 1;
  
  // Convert speeds to frames
  const initialDelayFrames = initialDelay * fps;
  const framesPerChar = fps / typingSpeed;
  const framesPerDeleteChar = fps / deletingSpeed;
  const pauseFrames = pauseDuration * fps;
  
  // Calculate timing for each text in the array
  let currentFrame = frame - initialDelayFrames;
  let displayedText = '';
  let isTyping = true;
  
  if (currentFrame < 0) {
    // Still in initial delay
    displayedText = '';
  } else {
    // Calculate which text we're on and where in its animation
    let textIndex = 0;
    
    for (let i = 0; i < textArray.length; i++) {
      const currentText = textArray[i];
      const typeFrames = currentText.length * framesPerChar;
      const deleteFrames = currentText.length * framesPerDeleteChar;
      
      if (currentFrame < typeFrames) {
        // Currently typing this text
        const charsToShow = Math.floor(currentFrame / framesPerChar);
        displayedText = currentText.substring(0, charsToShow);
        isTyping = true;
        break;
      }
      
      currentFrame -= typeFrames;
      
      if (!shouldLoop || i === textArray.length - 1) {
        // Last text - keep it displayed
        displayedText = currentText;
        isTyping = false;
        break;
      }
      
      // Pause before deleting
      if (currentFrame < pauseFrames) {
        displayedText = currentText;
        isTyping = false;
        break;
      }
      
      currentFrame -= pauseFrames;
      
      // Deleting phase
      if (currentFrame < deleteFrames) {
        const charsToRemove = Math.floor(currentFrame / framesPerDeleteChar);
        displayedText = currentText.substring(0, currentText.length - charsToRemove);
        isTyping = false;
        break;
      }
      
      currentFrame -= deleteFrames;
      
      // Brief pause before next text
      if (currentFrame < pauseFrames / 2) {
        displayedText = '';
        isTyping = true;
        break;
      }
      
      currentFrame -= pauseFrames / 2;
    }
  }
  
  // Cursor blink calculation
  const blinkCycle = fps / cursorBlinkSpeed;
  const cursorOpacity = showCursor 
    ? (Math.floor(frame / (blinkCycle / 2)) % 2 === 0 ? 1 : 0)
    : 0;
  
  return (
    <span 
      style={{
        display: 'inline-block',
        fontFamily: 'monospace',
        ...style
      }}
      className={className}
    >
      <span>{displayedText}</span>
      {showCursor && (
        <span
          style={{
            opacity: cursorOpacity,
            marginLeft: '2px',
          }}
        >
          {cursorCharacter}
        </span>
      )}
    </span>
  );
};
