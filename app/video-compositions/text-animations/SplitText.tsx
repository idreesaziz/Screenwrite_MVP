import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';

export interface SplitTextProps {
  text: string;
  animateBy?: 'letters' | 'words';
  direction?: 'top' | 'bottom';
  delay?: number;  // Delay between each letter/word in seconds
  duration?: number;  // Animation duration per letter/word in seconds
  style?: React.CSSProperties;
  className?: string;
}

/**
 * SplitText - Animates text by splitting into letters or words
 * Each letter/word animates in with a staggered delay
 */
export const SplitText: React.FC<SplitTextProps> = ({
  text,
  animateBy = 'letters',
  direction = 'top',
  delay = 0.05,
  duration = 0.5,
  style = {},
  className = '',
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  // Split text based on animateBy prop
  const parts = animateBy === 'letters' 
    ? text.split('') 
    : text.split(' ');
  
  // Calculate animation offset in pixels (matching original's y: 40)
  const offsetDistance = 40; // pixels to move from
  const yOffset = direction === 'top' ? -offsetDistance : offsetDistance;
  
  return (
    <span 
      style={{
        display: 'inline-block',
        ...style
      }}
      className={className}
    >
      {parts.map((part, index) => {
        // Calculate when this part should start animating (in frames)
        const startFrame = index * delay * fps;
        const endFrame = startFrame + (duration * fps);
        
        // GSAP power3.out easing - smooth deceleration (original)
        const power3Out = (t: number) => {
          const p = t - 1;
          return p * p * p + 1;
        };
        
        // Interpolate opacity
        const opacity = interpolate(
          frame,
          [startFrame, endFrame],
          [0, 1],
          {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
            easing: power3Out
          }
        );
        
        // Interpolate transform
        const translateY = interpolate(
          frame,
          [startFrame, endFrame],
          [yOffset, 0],
          {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
            easing: power3Out
          }
        );
        
        return (
          <span
            key={index}
            style={{
              display: 'inline-block',
              opacity,
              transform: `translateY(${translateY}px)`,
              // Preserve spaces for word-based animation
              whiteSpace: animateBy === 'words' ? 'pre' : 'normal',
            }}
          >
            {part}
            {/* Add space after each word except the last */}
            {animateBy === 'words' && index < parts.length - 1 && ' '}
          </span>
        );
      })}
    </span>
  );
};
