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
  
  // Handle click on empty space to deselect
  const handleOverlayClick = (event: React.MouseEvent) => {
    console.log('handleOverlayClick - deselecting');
    if (event.target === event.currentTarget) {
      onSelectClip(null);
    }
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
    
    // Select clip if not already selected
    if (selectedClipId !== clipId) {
      onSelectClip(clipId);
    }
  };
  
  // Handle mouse move during drag
  useEffect(() => {
    if (!isDragging || !dragStart || !selectedClipId) return;
    
    const handleMouseMove = (event: MouseEvent) => {
      const deltaX = event.clientX - dragStart.x;
      const deltaY = event.clientY - dragStart.y;
      
      if (dragHandle === null) {
        // Dragging the clip (translate)
        onUpdateTransform(selectedClipId, {
          translateX: deltaX,
          translateY: deltaY,
        });
      } else if (dragHandle === 'rotate') {
        // Rotating the clip
        // Calculate angle from center
        const selectedClipData = clipBounds.find(cb => cb.clip.id === selectedClipId);
        if (selectedClipData) {
          const centerX = selectedClipData.bounds.x + selectedClipData.bounds.width / 2;
          const centerY = selectedClipData.bounds.y + selectedClipData.bounds.height / 2;
          
          const angle = Math.atan2(event.clientY - centerY, event.clientX - centerX);
          const degrees = (angle * 180) / Math.PI;
          
          onUpdateTransform(selectedClipId, {
            rotation: degrees,
          });
        }
      } else {
        // Scaling from corner handle
        // For now, uniform scale based on distance from center
        const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
        const scale = 1 + distance / 200; // Adjust scaling sensitivity
        
        onUpdateTransform(selectedClipId, {
          scaleX: scale,
          scaleY: scale,
        });
      }
      
      // Update drag start for next delta
      setDragStart({ x: event.clientX, y: event.clientY });
    };
    
    const handleMouseUp = () => {
      setIsDragging(false);
      setDragStart(null);
      setDragHandle(null);
    };
    
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, dragStart, selectedClipId, dragHandle, clipBounds, onUpdateTransform]);
  
  console.log('TransformOverlay rendering with clipBounds:', clipBounds.length);
  
  return (
    <div
      ref={overlayRef}
      className="absolute inset-0"
      onClick={handleOverlayClick}
      style={{
        pointerEvents: 'auto', // Allow clicks to pass through to children
        // Remove explicit width/height - let it fill parent with inset-0
      }}
    >
      {clipBounds.length === 0 && (
        <div style={{ color: 'white', padding: 10 }}>No selectable clips at this frame</div>
      )}
      {clipBounds.map(({ clip, bounds, trackIndex }) => {
        const isSelected = clip.id === selectedClipId;
        
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
            {/* Clickable area - visible for debugging */}
            <div
              className={`absolute transition-all ${
                isSelected
                  ? 'border-2 border-primary bg-primary/5'
                  : 'border-2 border-green-500 bg-green-500/20 hover:border-primary hover:bg-primary/10'
              }`}
              style={{
                left: scaledBounds.x,
                top: scaledBounds.y,
                width: scaledBounds.width,
                height: scaledBounds.height,
                cursor: isSelected ? 'move' : 'pointer',
                pointerEvents: 'auto',
                zIndex: 50,
              }}
              onClick={(e) => {
                console.log('Click on clip div:', clip.id);
                e.stopPropagation();
                handleClipClick(clip.id, e);
              }}
              onMouseDown={(e) => {
                console.log('MouseDown on clip div:', clip.id, 'isSelected:', isSelected);
                if (isSelected) {
                  e.stopPropagation();
                  handleMouseDown(clip.id, null, e);
                }
              }}
              title={`${clip.id} (Track ${trackIndex + 1})`}
            >
              {/* Show handles and info only when selected */}
              {isSelected && (
                <>
                  {/* Clip info label - always visible when selected */}
                  <div
                    className="absolute bg-primary text-primary-foreground text-xs px-2 py-1 rounded pointer-events-none whitespace-nowrap"
                    style={{
                      left: 0,
                      top: -28,
                      zIndex: 100,
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
                    className="absolute bg-primary rounded-full cursor-grab active:cursor-grabbing"
                    style={{
                      width: 12,
                      height: 12,
                      left: '50%',
                      top: -30,
                      transform: 'translateX(-50%)',
                      zIndex: 100,
                    }}
                    onMouseDown={(e) => handleMouseDown(clip.id, 'rotate', e)}
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
                </>
              )}
            </div>
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
      className="absolute bg-background border-2 border-primary rounded"
      style={{
        width: 12,
        height: 12,
        ...positionStyles[position],
      }}
      onMouseDown={onMouseDown}
    />
  );
}
