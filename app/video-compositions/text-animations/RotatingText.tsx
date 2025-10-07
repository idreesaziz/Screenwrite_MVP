import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';

export interface RotatingTextProps {
  texts: string[];
  rotationInterval?: number; // seconds per text
  staggerDuration?: number; // seconds between character animations
  staggerFrom?: 'first' | 'last' | 'center';
  splitBy?: 'characters' | 'words';
  loop?: boolean;
  delay?: number;
  className?: string;
  style?: React.CSSProperties;
}

export const RotatingText: React.FC<RotatingTextProps> = ({
  texts,
  rotationInterval = 2,
  staggerDuration = 0.03,
  staggerFrom = 'first',
  splitBy = 'characters',
  loop = true,
  delay = 0,
  className = '',
  style = {},
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const delayFrames = delay * fps;
  const localFrame = frame - delayFrames;

  // Calculate current text index
  const intervalFrames = rotationInterval * fps;
  const currentCycle = Math.floor(localFrame / intervalFrames);
  const currentTextIndex = loop ? currentCycle % texts.length : Math.min(currentCycle, texts.length - 1);
  const frameInCycle = localFrame % intervalFrames;

  // Before animation
  if (localFrame < 0) {
    return (
      <span className={className} style={{ display: 'inline-block', ...style }}>
        {texts[0].toUpperCase()}
      </span>
    );
  }

  const currentText = texts[currentTextIndex].toUpperCase();

  // Split text based on splitBy mode
  const splitText = (): { characters: string[]; needsSpace: boolean }[] => {
    if (splitBy === 'characters') {
      const words = currentText.split(' ');
      return words.map((word, i) => ({
        characters: word.split(''),
        needsSpace: i !== words.length - 1,
      }));
    } else {
      // words mode
      return currentText.split(' ').map((word, i, arr) => ({
        characters: [word],
        needsSpace: i !== arr.length - 1,
      }));
    }
  };

  const elements = splitText();
  const totalChars = elements.reduce((sum, word) => sum + word.characters.length, 0);

  // Calculate stagger delay for each character
  const getStaggerDelay = (index: number): number => {
    if (staggerFrom === 'first') return index * staggerDuration;
    if (staggerFrom === 'last') return (totalChars - 1 - index) * staggerDuration;
    if (staggerFrom === 'center') {
      const center = Math.floor(totalChars / 2);
      return Math.abs(center - index) * staggerDuration;
    }
    return index * staggerDuration;
  };

  // Power3.out easing
  const power3Out = (t: number): number => {
    const x = t - 1;
    return x * x * x + 1;
  };

  // Calculate transition timing
  const transitionDuration = 0.5; // seconds for enter/exit
  const enterEnd = transitionDuration * fps;
  const exitStart = intervalFrames - transitionDuration * fps;

  let charGlobalIndex = 0;

  return (
    <span className={className} style={{ display: 'inline-block', ...style }}>
      {elements.map((wordObj, wordIndex) => (
        <span key={wordIndex} style={{ display: 'inline-block' }}>
          {wordObj.characters.map((char, charIndex) => {
            const currentCharIndex = charGlobalIndex++;
            const charDelayFrames = getStaggerDelay(currentCharIndex) * fps;

            // Calculate animation state
            let opacity = 1;
            let translateY = 0;

            if (frameInCycle < enterEnd) {
              // Entering animation
              const enterProgress = Math.max(0, (frameInCycle - charDelayFrames) / (enterEnd - charDelayFrames));
              const easedProgress = power3Out(Math.min(1, enterProgress));
              opacity = easedProgress;
              translateY = interpolate(easedProgress, [0, 1], [30, 0], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              });
            } else if (frameInCycle >= exitStart) {
              // Exiting animation
              const exitProgress = (frameInCycle - exitStart - charDelayFrames) / (transitionDuration * fps);
              const easedProgress = power3Out(Math.min(1, Math.max(0, exitProgress)));
              opacity = 1 - easedProgress;
              translateY = interpolate(easedProgress, [0, 1], [0, -40], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              });
            }

            return (
              <span
                key={charIndex}
                style={{
                  display: 'inline-block',
                  opacity,
                  transform: `translateY(${translateY}px)`,
                }}
              >
                {char}
              </span>
            );
          })}
          {wordObj.needsSpace && <span style={{ display: 'inline-block' }}> </span>}
        </span>
      ))}
    </span>
  );
};
