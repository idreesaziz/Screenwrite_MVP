import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';

export interface DecryptedTextProps {
  text: string;
  speed?: number; // characters revealed per second
  sequential?: boolean;
  revealDirection?: 'start' | 'end' | 'center';
  useOriginalCharsOnly?: boolean;
  characters?: string;
  delay?: number; // initial delay in seconds
  className?: string;
  style?: React.CSSProperties;
}

const DEFAULT_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!@#$%^&*()_+';

export const DecryptedText: React.FC<DecryptedTextProps> = ({
  text,
  speed = 10, // chars per second
  sequential = true,
  revealDirection = 'start',
  useOriginalCharsOnly = false,
  characters = DEFAULT_CHARS,
  delay = 0,
  className = '',
  style = {},
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const textUpper = text.toUpperCase();
  const delayFrames = delay * fps;
  const localFrame = frame - delayFrames;

  // Before animation starts
  if (localFrame < 0) {
    return (
      <span className={className} style={{ display: 'inline-block', whiteSpace: 'pre-wrap', ...style }}>
        {textUpper}
      </span>
    );
  }

  const availableChars = useOriginalCharsOnly
    ? Array.from(new Set(textUpper.split(''))).filter(char => char !== ' ')
    : characters.toUpperCase().split('');

  const getNextIndex = (revealedCount: number, textLength: number): number => {
    switch (revealDirection) {
      case 'start':
        return revealedCount;
      case 'end':
        return textLength - 1 - revealedCount;
      case 'center': {
        const middle = Math.floor(textLength / 2);
        const offset = Math.floor(revealedCount / 2);
        return revealedCount % 2 === 0 ? middle + offset : middle - offset - 1;
      }
      default:
        return revealedCount;
    }
  };

  // Calculate how many characters should be revealed
  const revealedCount = sequential
    ? Math.min(Math.floor((localFrame / fps) * speed), textUpper.length)
    : textUpper.length; // if not sequential, reveal all at once with scrambling

  // Build revealed indices set
  const revealedIndices = new Set<number>();
  if (sequential) {
    for (let i = 0; i < revealedCount; i++) {
      const idx = getNextIndex(i, textUpper.length);
      if (idx >= 0 && idx < textUpper.length) {
        revealedIndices.add(idx);
      }
    }
  }

  // Generate display text
  const displayChars = textUpper.split('').map((char, index) => {
    if (char === ' ') return ' ';
    
    if (sequential) {
      // In sequential mode, revealed chars show correct, others scramble
      if (revealedIndices.has(index)) {
        return char;
      } else {
        // Scramble unrevealed chars
        const seed = index * 1000 + frame;
        const charIndex = Math.abs(seed) % availableChars.length;
        return availableChars[charIndex] || char;
      }
    } else {
      // Non-sequential: all chars scramble then settle
      const charsPerSecond = speed;
      const settleFrame = (textUpper.length / charsPerSecond) * fps;
      
      if (localFrame >= settleFrame) {
        return char;
      } else {
        const seed = index * 1000 + frame;
        const charIndex = Math.abs(seed) % availableChars.length;
        return availableChars[charIndex] || char;
      }
    }
  });

  return (
    <span className={className} style={{ display: 'inline-block', whiteSpace: 'pre-wrap', ...style }}>
      {displayChars.map((char, index) => {
        const isRevealed = sequential
          ? revealedIndices.has(index)
          : localFrame >= (textUpper.length / speed) * fps;
        
        return (
          <span
            key={index}
            style={{
              display: 'inline-block',
              opacity: isRevealed ? 1 : 0.7,
            }}
          >
            {/* Replace spaces with non-breaking spaces for inline-block */}
            {char === ' ' ? '\u00A0' : char}
          </span>
        );
      })}
    </span>
  );
};
