import type { TransitionPresentation, TransitionPresentationComponentProps } from '@remotion/transitions';
import React, { useMemo } from 'react';
import { AbsoluteFill, interpolate } from 'remotion';

export type BlurPresentationProps = {
  width: number;
  height: number;
};

const BlurPresentation: React.FC<
  TransitionPresentationComponentProps<BlurPresentationProps>
> = ({ children, presentationDirection, presentationProgress }) => {
  const style: React.CSSProperties = useMemo(() => {
    // Blur both entering and exiting slides
    // Exiting: blur increases from 0 to 20px as it exits
    // Entering: blur decreases from 20px to 0 as it enters
    const blurAmount = interpolate(
      presentationProgress,
      [0, 1],
      presentationDirection === 'exiting' ? [0, 20] : [20, 0]
    );

    // Also add slight opacity fade for smoother crossfade
    const opacity = interpolate(
      presentationProgress,
      [0, 1],
      presentationDirection === 'exiting' ? [1, 0] : [0, 1]
    );

    return {
      width: '100%',
      height: '100%',
      filter: `blur(${blurAmount}px)`,
      opacity,
    };
  }, [presentationDirection, presentationProgress]);

  return (
    <AbsoluteFill>
      <AbsoluteFill style={style}>{children}</AbsoluteFill>
    </AbsoluteFill>
  );
};

export const blur = (
  props: BlurPresentationProps
): TransitionPresentation<BlurPresentationProps> => {
  return {
    component: BlurPresentation,
    props,
  };
};
