import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';

export interface GradientTextProps {
  text: string;
  colors?: string[];
  animationSpeed?: number; // seconds for full cycle
  showBorder?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

export const GradientText: React.FC<GradientTextProps> = ({
  text,
  colors = ['#40ffaa', '#4079ff', '#40ffaa', '#4079ff', '#40ffaa'],
  animationSpeed = 8,
  showBorder = false,
  className = '',
  style = {},
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Calculate animation progress (loops continuously)
  const totalFrames = animationSpeed * fps;
  const progress = (frame % totalFrames) / totalFrames;

  // Animate gradient by shifting background position
  const backgroundPosition = `${progress * 200}% center`;

  const gradientStyle: React.CSSProperties = {
    backgroundImage: `linear-gradient(to right, ${colors.join(', ')})`,
    backgroundSize: '200% auto',
    backgroundPosition,
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
  };

  const borderStyle: React.CSSProperties = showBorder
    ? {
        position: 'absolute',
        inset: 0,
        backgroundImage: `linear-gradient(to right, ${colors.join(', ')})`,
        backgroundSize: '200% auto',
        backgroundPosition,
        borderRadius: '0.5rem',
        opacity: 0.3,
        zIndex: -1,
      }
    : {};

  return (
    <div
      className={className}
      style={{
        position: 'relative',
        display: 'inline-block',
        ...style,
      }}
    >
      {showBorder && <div style={borderStyle}></div>}
      <div style={gradientStyle}>{text}</div>
    </div>
  );
};
