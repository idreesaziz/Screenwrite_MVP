import React, { useState, useRef, useEffect } from "react";
import type { CompositionBlueprint, Clip } from "../../video-compositions/BlueprintTypes";
import {
  getVisibleClips,
  calculateClipBounds,
  type BoundingBox,
  type TransformValues,
} from "../../utils/transformUtils";

interface TransformOverlayProps {
  composition: CompositionBlueprint;
  currentFrame: number;
  fps: number;
  compositionWidth: number;
  compositionHeight: number;
  selectedClipId: string | null;
  onSelectClip: (clipId: string | null) => void;
  onUpdateTransform: (clipId: string, transform: Partial<TransformValues>) => void;
  isPlaying: boolean;
}

type HandleType = 'tl' | 'tr' | 'bl' | 'br' | 'rotate' | null;

/**
 * TransformOverlay - Interactive layer for selecting and transforming clips
 * Renders selection boxes and transform handles over the video player
 */
export function TransformOverlay({
  composition,
  currentFrame,
  fps,
  compositionWidth,
  compositionHeight,
  selectedClipId,
  onSelectClip,
  onUpdateTransform,
  isPlaying,
}: TransformOverlayProps) {
  const overlayRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number } | null>(null);
  const [dragHandle, setDragHandle] = useState<HandleType>(null);
  const [hoveredClipId, setHoveredClipId] = useState<string | null>(null);
  const initialTransformRef = useRef<TransformValues | null>(null);
  const scaleStartInfoRef = useRef<{
    baseWidth: number;
    baseHeight: number;
    fixedCorner: { x: number; y: number }; // composition coords
    initialCenter: { x: number; y: number }; // composition coords
    rotationDeg: number;
    initialTransform: TransformValues;
  } | null>(null);
  const [displaySize, setDisplaySize] = useState({ 
    width: compositionWidth, 
    height: compositionHeight,
    offsetX: 0,
    offsetY: 0
  });
  
  // Measure actual player display size (accounting for aspect ratio letterboxing)
  useEffect(() => {
    if (!overlayRef.current) return;
    
    const updateSize = () => {
      if (!overlayRef.current) return;
      
      // Get the container size
      const containerRect = overlayRef.current.getBoundingClientRect();
      
      // Calculate the actual player size within the container
      // The player maintains aspect ratio, so it might be letterboxed
      const compositionAspectRatio = compositionWidth / compositionHeight;
      const containerAspectRatio = containerRect.width / containerRect.height;
      
      let playerWidth, playerHeight, playerOffsetX, playerOffsetY;
      
      if (containerAspectRatio > compositionAspectRatio) {
        // Container is wider than composition - letterbox on sides
        playerHeight = containerRect.height;
        playerWidth = playerHeight * compositionAspectRatio;
        playerOffsetX = (containerRect.width - playerWidth) / 2;
        playerOffsetY = 0;
      } else {
        // Container is taller than composition - letterbox on top/bottom
        playerWidth = containerRect.width;
        playerHeight = playerWidth / compositionAspectRatio;
        playerOffsetX = 0;
        playerOffsetY = (containerRect.height - playerHeight) / 2;
      }
      
      setDisplaySize({ 
        width: playerWidth, 
        height: playerHeight,
        offsetX: playerOffsetX,
        offsetY: playerOffsetY
      });
      
      console.log('Player size:', playerWidth, 'x', playerHeight, 'offset:', playerOffsetX, playerOffsetY);
      console.log('Container size:', containerRect.width, 'x', containerRect.height);
    };
    
    // Initial size
    updateSize();
    
    // Watch for resize events
    const resizeObserver = new ResizeObserver(updateSize);
    resizeObserver.observe(overlayRef.current);
    
    // Also listen to window resize
    window.addEventListener('resize', updateSize);
    
    return () => {
      resizeObserver.disconnect();
      window.removeEventListener('resize', updateSize);
    };
  }, [compositionWidth, compositionHeight]);
  
  // Calculate scale factors
  const scaleX = displaySize.width / compositionWidth;
  const scaleY = displaySize.height / compositionHeight;
  
  console.log('Scale factors:', scaleX, scaleY);
  
  // Get all clips visible at current frame
  const visibleClips = getVisibleClips(composition, currentFrame, fps);
  
  // Calculate bounding boxes for visible clips
  // Filter out clips with no selectable content (null bounds)
  const clipBounds = visibleClips
    .map(({ clip, trackIndex }) => {
      const bounds = calculateClipBounds(clip, compositionWidth, compositionHeight);
      console.log(`Clip "${clip.id}" bounds:`, bounds);
      return bounds ? { clip, trackIndex, bounds } : null;
    })
    .filter((item): item is NonNullable<typeof item> => item !== null);
  
  console.log('TransformOverlay - visible clips:', visibleClips.length, 'with bounds:', clipBounds.length);
  console.log('TransformOverlay - isPlaying:', isPlaying, 'currentFrame:', currentFrame);
  
  // Hide overlay when playing
  if (isPlaying) {
    return null;
  }
  
  // Handle click on clip to select it
  const handleClipClick = (clipId: string, event: React.MouseEvent) => {
    console.log('handleClipClick:', clipId);
    event.stopPropagation();
    onSelectClip(clipId);
  };
  
  // Helper function to check if a point is inside a rotated rectangle
  const isPointInRotatedRect = (
    pointX: number,
    pointY: number,
    rectX: number,
    rectY: number,
    rectWidth: number,
    rectHeight: number,
    rotation: number
  ): boolean => {
    // Calculate center of rectangle
    const centerX = rectX + rectWidth / 2;
    const centerY = rectY + rectHeight / 2;
    
    // Translate point to origin (relative to rect center)
    const translatedX = pointX - centerX;
    const translatedY = pointY - centerY;
    
    // Rotate point by negative rotation (inverse transform)
    const angleRad = (-rotation * Math.PI) / 180;
    const rotatedX = translatedX * Math.cos(angleRad) - translatedY * Math.sin(angleRad);
    const rotatedY = translatedX * Math.sin(angleRad) + translatedY * Math.cos(angleRad);
    
    // Check if rotated point is inside the non-rotated rectangle (centered at origin)
    const halfWidth = rectWidth / 2;
    const halfHeight = rectHeight / 2;
    
    return (
      rotatedX >= -halfWidth &&
      rotatedX <= halfWidth &&
      rotatedY >= -halfHeight &&
      rotatedY <= halfHeight
    );
  };

  // Handle clicks - find topmost clip at click position
  const handleOverlayClick = (event: React.MouseEvent) => {
    const rect = overlayRef.current?.getBoundingClientRect();
    if (!rect) return;
    
    // Get click position relative to overlay
    const clickX = event.clientX - rect.left;
    const clickY = event.clientY - rect.top;
    
    console.log('Overlay clicked at:', clickX, clickY, 'total clips:', clipBounds.length);
    
    // Find all clips at this position (iterate in reverse to get topmost first)
    let foundClip: string | null = null;
    const matchingClips: string[] = [];
    
    for (let i = clipBounds.length - 1; i >= 0; i--) {
      const { clip, bounds, trackIndex } = clipBounds[i];
      
      // Scale bounds to display coordinates
      const scaledBounds = {
        x: bounds.x * scaleX + displaySize.offsetX,
        y: bounds.y * scaleY + displaySize.offsetY,
        width: bounds.width * scaleX,
        height: bounds.height * scaleY,
      };
      
      const rotation = bounds.rotation || 0;
      
      console.log(`Checking clip ${clip.id} (track ${trackIndex}):`, 
        'click:', clickX, clickY,
        'bounds:', scaledBounds,
        'rotation:', rotation);
      
      // Check if click is within bounds (accounting for rotation)
      const isInside = isPointInRotatedRect(
        clickX,
        clickY,
        scaledBounds.x,
        scaledBounds.y,
        scaledBounds.width,
        scaledBounds.height,
        rotation
      );
      
      if (isInside) {
        matchingClips.push(clip.id);
        if (!foundClip) {
          foundClip = clip.id;
          console.log('✓ Found topmost clip at position:', clip.id, 'track:', trackIndex);
        }
      }
    }
    
    if (matchingClips.length > 0) {
      console.log('All matching clips at position:', matchingClips);
    } else {
      console.log('No clips found at click position - deselecting');
    }
    
    onSelectClip(foundClip);
  };
  
  // Handle mouse down on drag handle
  const handleMouseDown = (
    clipId: string,
    handle: HandleType,
    event: React.MouseEvent
  ) => {
    event.stopPropagation();
    setIsDragging(true);
    setDragHandle(handle);
    setDragStart({ x: event.clientX, y: event.clientY });
    
    // Find and store initial transform values
    const clipData = clipBounds.find(cb => cb.clip.id === clipId);
    if (clipData) {
      // Parse existing transform from the clip's first element
      const firstElement = clipData.clip.element.elements[0];
      if (firstElement) {
        const props = firstElement.split(';').reduce((acc, part) => {
          const [key, value] = part.split(':');
          if (key && value) acc[key] = value;
          return acc;
        }, {} as Record<string, string>);
        
        // Extract transform values
        const transformStr = props.transform || '';
        const translateMatch = transformStr.match(/translate\(([^,]+),\s*([^)]+)\)/);
        const scaleMatch = transformStr.match(/scale\(([^,]+)(?:,\s*([^)]+))?\)/);
        const rotateMatch = transformStr.match(/rotate\(([^)]+)\)/);
        
        initialTransformRef.current = {
          translateX: translateMatch ? parseFloat(translateMatch[1]) : 0,
          translateY: translateMatch ? parseFloat(translateMatch[2]) : 0,
          scaleX: scaleMatch ? parseFloat(scaleMatch[1]) : 1,
          scaleY: scaleMatch ? (scaleMatch[2] ? parseFloat(scaleMatch[2]) : parseFloat(scaleMatch[1])) : 1,
          rotation: rotateMatch ? parseFloat(rotateMatch[1]) : 0,
        };
      } else {
        initialTransformRef.current = {
          translateX: 0,
          translateY: 0,
          scaleX: 1,
          scaleY: 1,
          rotation: 0,
        };
      }
      // If starting a corner scale, capture anchor and base dimensions
      if (handle && handle !== 'rotate' && initialTransformRef.current) {
        const init = initialTransformRef.current;
        const bounds = clipData.bounds;
        const baseWidth = Math.max(1, bounds.width / Math.max(0.0001, init.scaleX));
        const baseHeight = Math.max(1, bounds.height / Math.max(0.0001, init.scaleY));
        const rotationDeg = bounds.rotation || 0;
        const center = { x: bounds.x + bounds.width / 2, y: bounds.y + bounds.height / 2 };
        const angle = (rotationDeg * Math.PI) / 180;
        const cos = Math.cos(angle);
        const sin = Math.sin(angle);
        const halfW = bounds.width / 2;
        const halfH = bounds.height / 2;
        const oppositeSignMap: Record<'tl'|'tr'|'bl'|'br', { sx: number; sy: number }> = {
          tl: { sx: 1, sy: 1 }, // opposite is br
          tr: { sx: -1, sy: 1 }, // opposite is bl
          bl: { sx: 1, sy: -1 }, // opposite is tr
          br: { sx: -1, sy: -1 }, // opposite is tl
        };
        const { sx, sy } = oppositeSignMap[handle];
        const fixedLocal = { x: sx * halfW, y: sy * halfH };
        const fixedWorld = {
          x: center.x + fixedLocal.x * cos - fixedLocal.y * sin,
          y: center.y + fixedLocal.x * sin + fixedLocal.y * cos,
        };
        scaleStartInfoRef.current = {
          baseWidth,
          baseHeight,
          fixedCorner: fixedWorld,
          initialCenter: center,
          rotationDeg,
          initialTransform: { ...init },
        };
      }
    }
    
    // Select clip if not already selected
    if (selectedClipId !== clipId) {
      onSelectClip(clipId);
    }
  };
  
  // Handle mouse move during drag
  useEffect(() => {
    if (!isDragging || !dragStart || !selectedClipId || !initialTransformRef.current) return;
    
    const handleMouseMove = (event: MouseEvent) => {
      const initialTransform = initialTransformRef.current!;
      
      // Calculate delta from initial drag start position
      const deltaX = event.clientX - dragStart.x;
      const deltaY = event.clientY - dragStart.y;
      
      // Convert screen-space pixels to composition-space pixels
      const compositionDeltaX = deltaX / scaleX;
      const compositionDeltaY = deltaY / scaleY;
      
      if (dragHandle === null) {
        // Dragging the clip (translate) - just add delta to initial position
        const newTransform = {
          translateX: initialTransform.translateX + compositionDeltaX,
          translateY: initialTransform.translateY + compositionDeltaY,
        };
        
        console.log('Translating clip:', selectedClipId, 'delta:', compositionDeltaX, compositionDeltaY, 'new:', newTransform);
        onUpdateTransform(selectedClipId, newTransform);
      } else if (dragHandle === 'rotate') {
        // Rotating the clip
        const selectedClipData = clipBounds.find(cb => cb.clip.id === selectedClipId);
        if (selectedClipData) {
          // Get center in display coordinates
          const centerX = (selectedClipData.bounds.x + selectedClipData.bounds.width / 2) * scaleX + displaySize.offsetX;
          const centerY = (selectedClipData.bounds.y + selectedClipData.bounds.height / 2) * scaleY + displaySize.offsetY;
          
          const angle = Math.atan2(event.clientY - centerY, event.clientX - centerX);
          const degrees = (angle * 180) / Math.PI;
          
          onUpdateTransform(selectedClipId, {
            rotation: degrees,
          });
        }
      } else {
        // Geometric scaling using fixed opposite corner with rotation awareness
        const info = scaleStartInfoRef.current;
        if (!info || !dragHandle) return;

        // Convert mouse to composition coords
        const rect = overlayRef.current?.getBoundingClientRect();
        if (!rect) return;
        const mouseX = (event.clientX - rect.left - displaySize.offsetX) / scaleX;
        const mouseY = (event.clientY - rect.top - displaySize.offsetY) / scaleY;

        // World delta from fixed to mouse
        const dx = mouseX - info.fixedCorner.x;
        const dy = mouseY - info.fixedCorner.y;

        // Rotate into local space (undo rotation)
        const ang = (info.rotationDeg * Math.PI) / 180;
        const cos = Math.cos(ang);
        const sin = Math.sin(ang);
        const lx = dx * cos + dy * sin;
        const ly = -dx * sin + dy * cos;

        // Prevent flipping: enforce expected sign
        const expected: Record<'tl'|'tr'|'bl'|'br', { sx: number; sy: number }> = {
          tl: { sx: -1, sy: -1 },
          tr: { sx: 1, sy: -1 },
          bl: { sx: -1, sy: 1 },
          br: { sx: 1, sy: 1 },
        };
  const { sx, sy } = expected[dragHandle];
  const MIN = 4;
  // Enforce expected sign and a minimum magnitude to avoid flipping/jitter
  const clampedLX = sx * Math.max(MIN, sx * lx);
  const clampedLY = sy * Math.max(MIN, sy * ly);

        // New width/height from fixed to dragged corner in local space
        const width = Math.max(MIN, Math.abs(clampedLX));
        const height = Math.max(MIN, Math.abs(clampedLY));
        const newScaleX = Math.max(0.05, width / info.baseWidth);
        const newScaleY = Math.max(0.05, height / info.baseHeight);

        // Midpoint becomes new center in world space
        const adjDx = clampedLX * cos - clampedLY * sin;
        const adjDy = clampedLX * sin + clampedLY * cos;
        const draggedX = info.fixedCorner.x + adjDx;
        const draggedY = info.fixedCorner.y + adjDy;
        const newCenterX = (info.fixedCorner.x + draggedX) / 2;
        const newCenterY = (info.fixedCorner.y + draggedY) / 2;

        const dcx = newCenterX - info.initialCenter.x;
        const dcy = newCenterY - info.initialCenter.y;

        onUpdateTransform(selectedClipId, {
          scaleX: newScaleX,
          scaleY: newScaleY,
          translateX: info.initialTransform.translateX + dcx,
          translateY: info.initialTransform.translateY + dcy,
        });
      }
    };
    
    const handleMouseUp = () => {
      setIsDragging(false);
      setDragStart(null);
      setDragHandle(null);
      initialTransformRef.current = null;
      scaleStartInfoRef.current = null;
    };
    
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, dragStart, selectedClipId, dragHandle, clipBounds, onUpdateTransform, scaleX, scaleY, displaySize]);
  
  console.log('TransformOverlay rendering with clipBounds:', clipBounds.length);
  
  return (
    <div
      ref={overlayRef}
      className="absolute inset-0"
      onClick={handleOverlayClick}
      style={{
        pointerEvents: 'auto',
      }}
    >
  {/* When no selectable clips, render nothing (hide the message) */}
      {clipBounds.map(({ clip, bounds, trackIndex }) => {
        const isSelected = clip.id === selectedClipId;
        const isHovered = clip.id === hoveredClipId;
        
        // Scale bounds from composition coordinates to display coordinates
        // and add letterbox offsets
        const scaledBounds = {
          x: bounds.x * scaleX + displaySize.offsetX,
          y: bounds.y * scaleY + displaySize.offsetY,
          width: bounds.width * scaleX,
          height: bounds.height * scaleY,
        };
        
        console.log('Rendering clip box:', clip.id, 'composition bounds:', bounds, 'scaled bounds:', scaledBounds, 'offsets:', displaySize.offsetX, displaySize.offsetY);
        
        return (
          <div key={clip.id}>
            {/* Selection box - only shown for selected clip */}
            {isSelected && (
              <>
              {/* Invisible drag area that covers the clip */}
              <div
                className="absolute transition-all"
                style={{
                  left: scaledBounds.x,
                  top: scaledBounds.y,
                  width: scaledBounds.width,
                  height: scaledBounds.height,
                  cursor: 'move',
                  pointerEvents: 'auto',
                  zIndex: 1000,
                  background: 'transparent',
                  transform: bounds.rotation ? `rotate(${bounds.rotation}deg)` : undefined,
                  transformOrigin: 'center',
                }}
                onMouseDown={(e) => {
                  console.log('MouseDown on selection box:', clip.id);
                  e.stopPropagation();
                  handleMouseDown(clip.id, null, e);
                }}
                title={`${clip.id} (Track ${trackIndex + 1})`}
              />
              {/* Visual border indicator (pointer-events none so it doesn't interfere) */}
              <div
                className="absolute border-2 border-primary bg-primary/10 pointer-events-none"
                style={{
                  left: scaledBounds.x,
                  top: scaledBounds.y,
                  width: scaledBounds.width,
                  height: scaledBounds.height,
                  zIndex: 999,
                  transform: bounds.rotation ? `rotate(${bounds.rotation}deg)` : undefined,
                  transformOrigin: 'center',
                }}
              />
              
              {/* Handles container - positioned relative to clip */}
              <div
                className="absolute pointer-events-none"
                style={{
                  left: scaledBounds.x,
                  top: scaledBounds.y,
                  width: scaledBounds.width,
                  height: scaledBounds.height,
                  zIndex: 1001,
                  transform: bounds.rotation ? `rotate(${bounds.rotation}deg)` : undefined,
                  transformOrigin: 'center',
                }}
              >
                {/* Clip info label */}
                <div
                  className="absolute bg-primary text-primary-foreground text-xs px-2 py-1 rounded whitespace-nowrap"
                  style={{
                    left: 0,
                    top: -28,
                  }}
                >
                  {clip.id} • Track {trackIndex + 1}
                </div>
                
                {/* Corner handles for scaling */}
                <Handle
                  position="tl"
                  onMouseDown={(e) => handleMouseDown(clip.id, 'tl', e)}
                />
                <Handle
                  position="tr"
                  onMouseDown={(e) => handleMouseDown(clip.id, 'tr', e)}
                />
                <Handle
                  position="bl"
                  onMouseDown={(e) => handleMouseDown(clip.id, 'bl', e)}
                />
                <Handle
                  position="br"
                  onMouseDown={(e) => handleMouseDown(clip.id, 'br', e)}
                />
                
                {/* Rotation handle */}
                <div
                  className="absolute bg-primary rounded-full cursor-grab active:cursor-grabbing pointer-events-auto"
                  style={{
                    width: 12,
                    height: 12,
                    left: '50%',
                    top: -30,
                    transform: 'translateX(-50%)',
                  }}
                  onMouseDown={(e) => {
                    e.stopPropagation();
                    handleMouseDown(clip.id, 'rotate', e);
                  }}
                >
                  {/* Line connecting to top edge */}
                  <div
                    className="absolute bg-primary"
                    style={{
                      width: 2,
                      height: 24,
                      left: '50%',
                      top: 12,
                      transform: 'translateX(-50%)',
                    }}
                  />
                </div>
              </div>
              </>
            )}
          </div>
        );
      })}
    </div>
  );
}

/**
 * Transform handle component (corner squares)
 */
interface HandleProps {
  position: 'tl' | 'tr' | 'bl' | 'br';
  onMouseDown: (event: React.MouseEvent) => void;
}

function Handle({ position, onMouseDown }: HandleProps) {
  const positionStyles = {
    tl: { left: -6, top: -6, cursor: 'nwse-resize' },
    tr: { right: -6, top: -6, cursor: 'nesw-resize' },
    bl: { left: -6, bottom: -6, cursor: 'nesw-resize' },
    br: { right: -6, bottom: -6, cursor: 'nwse-resize' },
  };
  
  return (
    <div
      className="absolute bg-background border-2 border-primary rounded pointer-events-auto"
      style={{
        width: 12,
        height: 12,
        ...positionStyles[position],
      }}
      onMouseDown={(e) => {
        e.stopPropagation();
        onMouseDown(e);
      }}
    />
  );
}
