import type { TransitionPresentation, TransitionPresentationComponentProps } from '@remotion/transitions';
import React, { useMemo } from 'react';
import { AbsoluteFill, interpolate, random } from 'remotion';

export type GlitchPresentationProps = {
  width: number;
  height: number;
};

const GlitchPresentation: React.FC<
  TransitionPresentationComponentProps<GlitchPresentationProps>
> = ({ children, presentationDirection, presentationProgress }) => {
  const isEntering = presentationDirection === 'entering';
  const progress = presentationProgress;

  // Crossfade for both lanes to avoid hard cuts
  const laneOpacity = isEntering
    ? interpolate(progress, [0, 1], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })
    : interpolate(progress, [0, 1], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  // Trigger short glitch bursts on discrete ticks
  const tick = Math.floor(progress * 24); // 24 checks over the transition
  const burstActive = random(`glitch-burst-${tick}`) > 0.6;

  // Shape intensity: peak around the middle, but only if a burst is active
  const baseIntensity = interpolate(progress, [0, 0.25, 0.5, 0.75, 1], [0, 1, 0.9, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const intensity = burstActive ? baseIntensity : 0;

  // Subtle per-lane jitter
  const jitterX = (random(`glitch-jx-${tick}-${isEntering ? 'in' : 'out'}`) - 0.5) * (isEntering ? 4 : 2) * (0.5 + intensity);
  const jitterY = (random(`glitch-jy-${tick}-${isEntering ? 'in' : 'out'}`) - 0.5) * (isEntering ? 2 : 1) * (0.5 + intensity);

  const baseStyle: React.CSSProperties = useMemo(() => {
    return {
      width: '100%',
      height: '100%',
      opacity: laneOpacity,
      transform: `translate(${jitterX}px, ${jitterY}px)`,
      willChange: 'transform, opacity',
    };
  }, [laneOpacity, jitterX, jitterY]);

  // Build horizontal slice offsets for entering lane during bursts
  const slices = useMemo(() => {
    if (!isEntering || intensity === 0) return null;

    const count = 6;
    const elements: React.ReactNode[] = [];
    for (let i = 0; i < count; i++) {
      const topPct = (i / count) * 100 + (random(`glitch-top-${tick}-${i}`) - 0.5) * 2; // +-2%
      const heightPct = 100 / count * (0.85 + random(`glitch-h-${tick}-${i}`) * 0.3); // 85%-115% of segment
      const shift = (random(`glitch-shift-${tick}-${i}`) - 0.5) * 2 * (8 + intensity * 12); // px

      const wrapper: React.CSSProperties = {
        position: 'absolute',
        left: 0,
        right: 0,
        top: `${topPct}%`,
        height: `${heightPct}%`,
        overflow: 'hidden',
        pointerEvents: 'none',
        opacity: 0.9,
      };

      const inner: React.CSSProperties = {
        transform: `translateX(${shift}px)`,
        willChange: 'transform',
      };

      elements.push(
        <div key={`glitch-slice-${i}`} style={wrapper}>
          <AbsoluteFill style={inner}>{children}</AbsoluteFill>
        </div>
      );
    }
    return elements;
  }, [isEntering, intensity, tick, children]);

  // Chromatic aberration: subtle RGB split during bursts (entering only)
  const chromaLayers = useMemo(() => {
    if (!isEntering || intensity === 0) return null;
    const dx = 2 + intensity * 6; // 2-8px
    const common: React.CSSProperties = {
      mixBlendMode: 'screen',
      opacity: 0.28 + intensity * 0.22,
      willChange: 'transform, filter, opacity',
    } as React.CSSProperties;

    const redStyle: React.CSSProperties = {
      ...common,
      transform: `translateX(${dx}px)`,
      filter: 'hue-rotate(10deg) saturate(1.4)',
    };
    const cyanStyle: React.CSSProperties = {
      ...common,
      transform: `translateX(${-dx}px)`,
      filter: 'hue-rotate(300deg) saturate(1.4)',
    };

    return (
      <>
        <AbsoluteFill style={redStyle}>{children}</AbsoluteFill>
        <AbsoluteFill style={cyanStyle}>{children}</AbsoluteFill>
      </>
    );
  }, [isEntering, intensity, children]);

  // Scanline overlay
  const scanlines = useMemo(() => {
    if (!isEntering || intensity === 0) return null;
    return (
      <AbsoluteFill
        style={{
          pointerEvents: 'none',
          opacity: 0.06 + intensity * 0.08,
          mixBlendMode: 'overlay',
          backgroundImage: 'repeating-linear-gradient(0deg, rgba(255,255,255,0.08), rgba(255,255,255,0.08) 1px, transparent 1px, transparent 3px)',
        }}
      />
    );
  }, [isEntering, intensity]);

  return (
    <AbsoluteFill>
      {/* Base lane content with controlled fade and subtle jitter */}
      <AbsoluteFill style={baseStyle}>{children}</AbsoluteFill>

      {/* Entering lane glitch layers */}
      {slices}
      {chromaLayers}
      {scanlines}
    </AbsoluteFill>
  );
};

export const glitch = (
  props: GlitchPresentationProps
): TransitionPresentation<GlitchPresentationProps> => {
  return {
    component: GlitchPresentation,
    props,
  };
};
