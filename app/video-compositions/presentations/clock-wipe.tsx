import type { TransitionPresentation, TransitionPresentationComponentProps } from '@remotion/transitions';
import React from 'react';
import { AbsoluteFill, interpolate } from 'remotion';

export type ClockWipePresentationProps = {
  width: number;
  height: number;
};

const ClockWipePresentation: React.FC<
  TransitionPresentationComponentProps<ClockWipePresentationProps>
> = ({ children, presentationDirection, presentationProgress }) => {
  const isEntering = presentationDirection === 'entering';
  
  // For entering: 0 -> 360 degrees (clockwise reveal)
  // For exiting: 360 -> 0 degrees (clockwise hide)
  const angle = isEntering
    ? interpolate(presentationProgress, [0, 1], [0, 360])
    : interpolate(presentationProgress, [0, 1], [360, 0]);

  // Opacity for smooth transition
  const opacity = isEntering
    ? interpolate(presentationProgress, [0, 0.1], [0, 1])
    : interpolate(presentationProgress, [0.9, 1], [1, 0]);

  // Create a conic gradient clip path
  const clipPath = `polygon(
    50% 50%,
    50% 0%,
    ${50 + 50 * Math.sin((angle * Math.PI) / 180)}% ${50 - 50 * Math.cos((angle * Math.PI) / 180)}%
  )`;

  return (
    <AbsoluteFill>
      <AbsoluteFill 
        style={{
          opacity,
          clipPath: angle >= 360 ? 'none' : clipPath,
        }}
      >
        {children}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const clockWipe = (
  props: ClockWipePresentationProps
): TransitionPresentation<ClockWipePresentationProps> => {
  return {
    component: ClockWipePresentation,
    props,
  };
};
