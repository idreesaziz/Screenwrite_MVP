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
        // stagger calc
        let charDelay = baseDelayFrames;
        if (animationMode === 'evenodd') {
          const odd = i % 2 === 1;
          const pos = Math.floor(i / 2);
          if (odd) {
            charDelay += pos * stagger * fps;
          } else {
            const oddCount = Math.ceil(chars.length / 2);
            const oddDuration = duration * fps + Math.max(0, oddCount - 1) * stagger * fps;
            charDelay += oddDuration * 0.7 + pos * stagger * fps;
          }
        } else {
          charDelay += i * stagger * fps;
        }

        const localFrame = frame - charDelay;
        const prog = interpolate(localFrame, [0, duration * fps], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
          easing: power3Out,
        });

        // Simple slide animation - character stays the same (F -> F)
        const glyph = ch;
        const color = colorForProgress(prog);
        
        // Simple horizontal slide effect - slides in place
        const slideDistance = 30; // pixels to slide
        const translateX = interpolate(prog, [0, 0.5, 1], [slideDistance, 0, 0], {
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
