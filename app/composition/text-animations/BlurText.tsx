import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';

export interface BlurTextProps {
  text: string;
  animateBy?: 'letters' | 'words';
  direction?: 'top' | 'bottom';
  delay?: number;  // Delay between each letter/word in seconds
  duration?: number;  // Total animation duration per letter/word in seconds
  style?: React.CSSProperties;
  className?: string;
}

/**
 * BlurText - Animates text with blur effect
 * Each letter/word fades in from blurred to sharp with staggered delay
 */
export const BlurText: React.FC<BlurTextProps> = ({
  text,
  animateBy = 'words',
  direction = 'top',
  delay = 0.2,
  duration = 0.7,  // Total duration for the multi-step animation
  style = {},
  className = '',
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  // Split text based on animateBy prop
  const parts = animateBy === 'letters' 
    ? text.split('') 
    : text.split(' ');
  
  // Calculate animation offset in pixels
  const offsetDistance = 50;
  const yOffset = direction === 'top' ? -offsetDistance : offsetDistance;
  
  return (
    <span 
      style={{
        display: 'inline-flex',
        flexWrap: 'wrap',
        ...style
      }}
      className={className}
    >
      {parts.map((part, index) => {
        // Calculate timing for this part
        const startFrame = index * delay * fps;
        const endFrame = startFrame + (duration * fps);
        
        // Animation happens continuously from start to end
        // Blur clears gradually while text is still moving
        
        // GSAP power3.out easing
        const power3Out = (t: number) => {
          const p = t - 1;
          return p * p * p + 1;
        };
        
        // Single continuous animation:
        // Blur clears gradually from start to end while text moves
        // Start: blur(15px), opacity 0, y offset
        // End: blur(0px), opacity 1, y at 0
        
        const blur = interpolate(
          frame,
          [startFrame, endFrame],
          [15, 0],
          {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
            easing: power3Out
          }
        );
        
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
              filter: `blur(${blur}px)`,
              willChange: 'transform, filter, opacity',
              whiteSpace: animateBy === 'words' ? 'pre' : 'normal',
            }}
          >
            {part === ' ' ? '\u00A0' : part}
            {animateBy === 'words' && index < parts.length - 1 && '\u00A0'}
          </span>
        );
      })}
    </span>
  );
};
