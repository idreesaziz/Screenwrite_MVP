import type { TransitionPresentation, TransitionPresentationComponentProps } from '@remotion/transitions';
import React, { useMemo } from 'react';
import { AbsoluteFill, interpolate } from 'remotion';

export type ZoomPresentationProps = {
  width: number;
  height: number;
  direction: 'in' | 'out';
};

const ZoomPresentation: React.FC<
  TransitionPresentationComponentProps<ZoomPresentationProps>
> = ({ children, presentationDirection, presentationProgress, passedProps }) => {
  const direction = passedProps.direction;
  const isEntering = presentationDirection === 'entering';

  // Define ranges per direction + lane (entering/exiting)
  const [scaleFrom, scaleTo] = (() => {
    if (isEntering) {
      // Entering lane
      return direction === 'in' ? [0.2, 1] : [1, 1];
    }
    // Exiting lane
    return direction === 'in' ? [1, 1] : [1, 3];
  })();

  const [opacityFrom, opacityTo] = (() => {
    if (isEntering) {
      // Entering always fades in
      return [0, 1];
    }
    // Exiting always fades out
    return [1, 0];
  })();

  const scale = interpolate(presentationProgress, [0, 1], [scaleFrom, scaleTo], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const opacity = interpolate(presentationProgress, [0, 1], [opacityFrom, opacityTo], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const style: React.CSSProperties = useMemo(() => {
    return {
      width: '100%',
      height: '100%',
      transform: `scale(${scale})`,
      transformOrigin: 'center center',
      opacity,
    };
  }, [scale, opacity]);

  return (
    <AbsoluteFill>
      <AbsoluteFill style={style}>{children}</AbsoluteFill>
    </AbsoluteFill>
  );
};

export const zoomIn = (
  props: Omit<ZoomPresentationProps, 'direction'>
): TransitionPresentation<ZoomPresentationProps> => {
  return {
    component: ZoomPresentation,
    props: { ...props, direction: 'in' },
  };
};

export const zoomOut = (
  props: Omit<ZoomPresentationProps, 'direction'>
): TransitionPresentation<ZoomPresentationProps> => {
  return {
    component: ZoomPresentation,
    props: { ...props, direction: 'out' },
  };
};
