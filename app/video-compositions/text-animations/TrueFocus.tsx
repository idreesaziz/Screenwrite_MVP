import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';

export interface TrueFocusProps {
  text: string;
  blurAmount?: number;
  borderColor?: string;
  glowColor?: string;
  animationDuration?: number; // seconds per word
  pauseBetweenAnimations?: number; // seconds to pause on each word
  delay?: number;
  className?: string;
  style?: React.CSSProperties;
}

export const TrueFocus: React.FC<TrueFocusProps> = ({
  text,
  blurAmount = 5,
  borderColor = '#00ff00',
  glowColor = 'rgba(0, 255, 0, 0.6)',
  animationDuration = 0.5,
  pauseBetweenAnimations = 1,
  delay = 0,
  className = '',
  style = {},
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const words = text.toUpperCase().split(' ');
  const delayFrames = delay * fps;
  const localFrame = frame - delayFrames;

  // Calculate which word is currently in focus
  const cycleDuration = (animationDuration + pauseBetweenAnimations) * fps;
  const currentCycle = Math.floor(localFrame / cycleDuration);
  const currentIndex = currentCycle % words.length;
  const frameInCycle = localFrame % cycleDuration;

  // Calculate transition progress for smooth animation
  const transitionFrames = animationDuration * fps;
  const transitionProgress = Math.min(frameInCycle / transitionFrames, 1);

  // Before animation
  if (localFrame < 0) {
    return (
      <span className={className} style={{ display: 'inline-block', whiteSpace: 'pre', ...style }}>
        {words.map((word, i) => (
          <span
            key={i}
            style={{
              display: 'inline-block',
              marginRight: i < words.length - 1 ? '0.5em' : 0,
              filter: 'blur(0px)',
            }}
          >
            {word}
          </span>
        ))}
      </span>
    );
  }

  // Calculate positions for sliding border
  let accumulatedWidth = 0;
  const wordPositions = words.map((word, i) => {
    const pos = accumulatedWidth;
    // Approximate width: 0.6em per char + 0.5em space
    const wordWidth = word.length * 0.6;
    accumulatedWidth += wordWidth + (i < words.length - 1 ? 0.5 : 0);
    return { left: pos, width: wordWidth };
  });

  const previousIndex = (currentIndex - 1 + words.length) % words.length;
  const currentPos = wordPositions[currentIndex];
  const prevPos = wordPositions[previousIndex];

  // Interpolate border position for smooth sliding
  const borderLeft = interpolate(
    transitionProgress,
    [0, 1],
    [prevPos.left, currentPos.left],
    {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    }
  );

  const borderWidth = interpolate(
    transitionProgress,
    [0, 1],
    [prevPos.width, currentPos.width],
    {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    }
  );

  return (
    <span
      className={className}
      style={{
        display: 'inline-block',
        position: 'relative',
        whiteSpace: 'pre',
        ...style,
      }}
    >
      {words.map((word, index) => {
        const isActive = index === currentIndex;
        const wasPreviouslyActive = index === previousIndex;

        // Calculate blur for smooth transitions
        let blur = blurAmount;
        if (isActive) {
          blur = interpolate(transitionProgress, [0, 1], [blurAmount, 0], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
        } else if (wasPreviouslyActive && frameInCycle < transitionFrames) {
          blur = interpolate(transitionProgress, [0, 1], [0, blurAmount], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
        }

        return (
          <span
            key={index}
            style={{
              display: 'inline-block',
              marginRight: index < words.length - 1 ? '0.5em' : 0,
              filter: `blur(${blur}px)`,
            }}
          >
            {word}
          </span>
        );
      })}
      
      {/* Sliding focus border */}
      <span
        style={{
          position: 'absolute',
          left: `${borderLeft}em`,
          top: '-6px',
          width: `${borderWidth}em`,
          height: 'calc(100% + 12px)',
          border: `2px solid ${borderColor}`,
          borderRadius: '6px',
          boxShadow: `0 0 15px ${glowColor}, inset 0 0 10px ${glowColor}`,
          pointerEvents: 'none',
          background: `linear-gradient(135deg, ${glowColor}08, transparent)`,
        }}
      >
        {/* Enhanced corner decorations */}
        <span
          style={{
            position: 'absolute',
            top: '-3px',
            left: '-3px',
            width: '12px',
            height: '12px',
            borderTop: `3px solid ${borderColor}`,
            borderLeft: `3px solid ${borderColor}`,
            boxShadow: `0 0 8px ${glowColor}`,
          }}
        />
        <span
          style={{
            position: 'absolute',
            top: '-3px',
            right: '-3px',
            width: '12px',
            height: '12px',
            borderTop: `3px solid ${borderColor}`,
            borderRight: `3px solid ${borderColor}`,
            boxShadow: `0 0 8px ${glowColor}`,
          }}
        />
        <span
          style={{
            position: 'absolute',
            bottom: '-3px',
            left: '-3px',
            width: '12px',
            height: '12px',
            borderBottom: `3px solid ${borderColor}`,
            borderLeft: `3px solid ${borderColor}`,
            boxShadow: `0 0 8px ${glowColor}`,
          }}
        />
        <span
          style={{
            position: 'absolute',
            bottom: '-3px',
            right: '-3px',
            width: '12px',
            height: '12px',
            borderBottom: `3px solid ${borderColor}`,
            borderRight: `3px solid ${borderColor}`,
            boxShadow: `0 0 8px ${glowColor}`,
          }}
        />
      </span>
    </span>
  );
};
