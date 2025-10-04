import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';

export interface ShuffleProps {
  text: string;
  duration?: number;
  delay?: number;
  stagger?: number;
  shuffleTimes?: number;
  animationMode?: 'evenodd' | 'sequential';
  scrambleCharset?: string;
  colorFrom?: string;
  colorTo?: string;
  shuffleDirection?: 'left' | 'right'; // kept for API compatibility
  className?: string;
  style?: React.CSSProperties;
}

const DEFAULT_CHARSET =
  'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*';

const power3Out = (t: number) => {
  const x = t - 1;
  return x * x * x + 1;
};

const hexToRgb = (hex: string) => {
  const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return m ? { r: parseInt(m[1], 16), g: parseInt(m[2], 16), b: parseInt(m[3], 16) } : null;
};

const rgbToHex = (r: number, g: number, b: number) =>
  '#' +
  [r, g, b]
    .map((v) => {
      const h = Math.max(0, Math.min(255, v)).toString(16);
      return h.length === 1 ? '0' + h : h;
    })
    .join('');

export const Shuffle: React.FC<ShuffleProps> = ({
  text,
  duration = 0.35,
  delay = 0,
  stagger = 0.03,
  shuffleTimes = 4,
  animationMode = 'sequential',
  scrambleCharset = DEFAULT_CHARSET,
  colorFrom,
  colorTo,
  shuffleDirection, // kept for API compatibility
  className = '',
  style = {},
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const chars = text.toUpperCase().split('');
  const baseDelayFrames = Math.max(0, delay * fps);

  const colorForProgress = (p: number) => {
    if (!colorFrom || !colorTo) return style.color;
    const a = hexToRgb(colorFrom);
    const b = hexToRgb(colorTo);
    if (!a || !b) return style.color;
    const r = Math.round(a.r + (b.r - a.r) * p);
    const g = Math.round(a.g + (b.g - a.g) * p);
    const bl = Math.round(a.b + (b.b - a.b) * p);
    return rgbToHex(r, g, bl);
  };

  return (
    <span className={className} style={{ display: 'inline-block', whiteSpace: 'pre-wrap', ...style }}>
      {chars.map((ch, i) => {
        // Two-phase animation:
        // Phase 1: Even-indexed letters shuffle (first half)
        // Phase 2: Odd-indexed letters shuffle (second half)
        
        const isEven = i % 2 === 0;
        const halfDuration = duration / 2;
        
        let charDelay = baseDelayFrames;
        if (isEven) {
          // Even letters animate in first half
          charDelay += (i / 2) * stagger * fps;
        } else {
          // Odd letters animate in second half
          charDelay += halfDuration * fps + ((i - 1) / 2) * stagger * fps;
        }

        const localFrame = frame - charDelay;
        const prog = interpolate(localFrame, [0, halfDuration * fps], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
          easing: power3Out,
        });

        // Character always visible, just slides in place
        const glyph = ch;
        const color = colorForProgress(prog);
        
        // Slide horizontally in place - starts at position, slides out and back
        const slideDistance = 30;
        const translateX = interpolate(prog, [0, 0.5, 1], [0, slideDistance, 0], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });

        return (
          <span
            key={i}
            style={{
              display: 'inline-block',
              overflow: 'hidden',
              position: 'relative',
            }}
          >
            <span
              style={{
                display: 'inline-block',
                color,
                transform: `translateX(${translateX}px)`,
              }}
            >
              {glyph}
            </span>
          </span>
        );
      })}
    </span>
  );
};
