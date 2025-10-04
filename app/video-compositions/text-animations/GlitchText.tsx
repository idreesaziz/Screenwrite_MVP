import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';

export interface GlitchTextProps {
  text: string;
  speed?: number;
  enableShadows?: boolean;
  shadowColors?: { red: string; cyan: string };
  glitchIntensity?: number;
  delay?: number;
  fontSize?: string;
  fontWeight?: string;
  color?: string;
  backgroundColor?: string;
}

export const GlitchText: React.FC<GlitchTextProps> = ({
  text,
  speed = 1,
  enableShadows = true,
  shadowColors = { red: '#ff0000', cyan: '#00ffff' },
  glitchIntensity = 10,
  delay = 0,
  fontSize = '128px',
  fontWeight = '900',
  color = '#ffffff',
  backgroundColor = '#060010',
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  const localFrame = Math.max(0, frame - delay * fps);
  
  // Calculate animation cycles based on speed
  const afterCycleDuration = (3 / speed) * fps;
  const beforeCycleDuration = (2 / speed) * fps;
  
  const afterProgress = (localFrame % afterCycleDuration) / afterCycleDuration;
  const beforeProgress = (localFrame % beforeCycleDuration) / beforeCycleDuration;
  
  // Generate clip-path values based on keyframes
  const getClipPath = (progress: number): string => {
    const keyframes = [
      { at: 0.00, value: 'inset(20% 0 50% 0)' },
      { at: 0.05, value: 'inset(10% 0 60% 0)' },
      { at: 0.10, value: 'inset(15% 0 55% 0)' },
      { at: 0.15, value: 'inset(25% 0 35% 0)' },
      { at: 0.20, value: 'inset(30% 0 40% 0)' },
      { at: 0.25, value: 'inset(40% 0 20% 0)' },
      { at: 0.30, value: 'inset(10% 0 60% 0)' },
      { at: 0.35, value: 'inset(15% 0 55% 0)' },
      { at: 0.40, value: 'inset(25% 0 35% 0)' },
      { at: 0.45, value: 'inset(30% 0 40% 0)' },
      { at: 0.50, value: 'inset(20% 0 50% 0)' },
      { at: 0.55, value: 'inset(10% 0 60% 0)' },
      { at: 0.60, value: 'inset(15% 0 55% 0)' },
      { at: 0.65, value: 'inset(25% 0 35% 0)' },
      { at: 0.70, value: 'inset(30% 0 40% 0)' },
      { at: 0.75, value: 'inset(40% 0 20% 0)' },
      { at: 0.80, value: 'inset(20% 0 50% 0)' },
      { at: 0.85, value: 'inset(10% 0 60% 0)' },
      { at: 0.90, value: 'inset(15% 0 55% 0)' },
      { at: 0.95, value: 'inset(25% 0 35% 0)' },
      { at: 1.00, value: 'inset(30% 0 40% 0)' },
    ];
    
    // Find the two keyframes to interpolate between
    let prevKeyframe = keyframes[0];
    let nextKeyframe = keyframes[keyframes.length - 1];
    
    for (let i = 0; i < keyframes.length - 1; i++) {
      if (progress >= keyframes[i].at && progress <= keyframes[i + 1].at) {
        prevKeyframe = keyframes[i];
        nextKeyframe = keyframes[i + 1];
        break;
      }
    }
    
    // For simplicity, return the closest keyframe value
    return progress - prevKeyframe.at < nextKeyframe.at - progress 
      ? prevKeyframe.value 
      : nextKeyframe.value;
  };
  
  const afterClipPath = getClipPath(afterProgress);
  const beforeClipPath = getClipPath(beforeProgress);
  
  const afterLeftOffset = glitchIntensity;
  const beforeLeftOffset = -glitchIntensity;
  
  const afterShadow = enableShadows ? `-${glitchIntensity / 2}px 0 ${shadowColors.red}` : 'none';
  const beforeShadow = enableShadows ? `${glitchIntensity / 2}px 0 ${shadowColors.cyan}` : 'none';
  
  const baseStyle: React.CSSProperties = {
    position: 'relative',
    color,
    fontSize,
    fontWeight,
    whiteSpace: 'nowrap',
    margin: '0 auto',
    userSelect: 'none',
  };
  
  const pseudoBaseStyle: React.CSSProperties = {
    position: 'absolute',
    top: 0,
    left: 0,
    color,
    backgroundColor,
    overflow: 'hidden',
    width: '100%',
    height: '100%',
  };
  
  const afterStyle: React.CSSProperties = {
    ...pseudoBaseStyle,
    left: `${afterLeftOffset}px`,
    textShadow: afterShadow,
    clipPath: afterClipPath,
  };
  
  const beforeStyle: React.CSSProperties = {
    ...pseudoBaseStyle,
    left: `${beforeLeftOffset}px`,
    textShadow: beforeShadow,
    clipPath: beforeClipPath,
  };
  
  return (
    <div style={baseStyle}>
      <span style={{ position: 'relative', zIndex: 1 }}>{text}</span>
      <span style={beforeStyle}>{text}</span>
      <span style={afterStyle}>{text}</span>
    </div>
  );
};
