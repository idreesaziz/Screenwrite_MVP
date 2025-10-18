import type { TransitionPresentation, TransitionPresentationComponentProps } from '@remotion/transitions';
import React from 'react';
import { AbsoluteFill, interpolate } from 'remotion';

export type IrisPresentationProps = {
  width: number;
  height: number;
};

const IrisPresentation: React.FC<
  TransitionPresentationComponentProps<IrisPresentationProps>
> = ({ children, presentationDirection, presentationProgress }) => {
  const isEntering = presentationDirection === 'entering';
  
  // For entering: grow from 0% to 150% (circular reveal from center)
  // For exiting: shrink from 150% to 0% (circular hide to center)
  const scale = isEntering
    ? interpolate(presentationProgress, [0, 1], [0, 1.5])
    : interpolate(presentationProgress, [0, 1], [1.5, 0]);

  // Opacity for smooth start/end
  const opacity = isEntering
    ? interpolate(presentationProgress, [0, 0.05], [0, 1])
    : interpolate(presentationProgress, [0.95, 1], [1, 0]);

  return (
    <AbsoluteFill>
      <AbsoluteFill 
        style={{
          opacity,
          clipPath: `circle(${scale * 70.7}% at 50% 50%)`, // 70.7% ensures full coverage at corners
          transform: 'translate(0, 0)', // Ensure clip-path is relative to element
        }}
      >
        {children}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const iris = (
  props: IrisPresentationProps
): TransitionPresentation<IrisPresentationProps> => {
  return {
    component: IrisPresentation,
    props,
  };
};
