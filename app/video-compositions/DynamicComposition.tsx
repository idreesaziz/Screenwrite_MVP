import React, { useState, useEffect } from "react";
import * as Remotion from "remotion";
import { Player, type PlayerRef } from "@remotion/player";
import { interp } from "../utils/animations";
import { BlueprintComposition } from "./BlueprintComposition";
import { calculateBlueprintDuration } from "./executeClipElement";
import type { CompositionBlueprint } from "./BlueprintTypes";
import { Play, Pause, Maximize, Volume2, VolumeX } from "lucide-react";
import { TransformOverlay } from "../components/editor/TransformOverlay";

// Destructure commonly used components for convenience
const { 
  AbsoluteFill, 
  useCurrentFrame, 
  interpolate, 
  Sequence, 
  Img, 
  Video, 
  Audio, 
  spring, 
  useVideoConfig,
  useCurrentScale,
  Easing
} = Remotion;

export interface DynamicCompositionProps {
  blueprint?: CompositionBlueprint;
  backgroundColor?: string;
  fps?: number;
}

// Dynamic composition that renders blueprint-based compositions only
export function DynamicComposition({
  blueprint,
  backgroundColor = "#000000",
}: DynamicCompositionProps) {

  // Blueprint-based rendering
  if (blueprint) {
    console.log("Rendering blueprint composition with", blueprint.length, "tracks");
    return (
      <BlueprintComposition 
        blueprint={blueprint} 
      />
    );
  }

  // No content placeholder
  return (
    <div style={{ backgroundColor, width: "100%", height: "100%" }}>
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "white",
          fontSize: "24px",
          fontFamily: "Arial, sans-serif",
        }}
      >
        No content to display
      </div>
    </div>
  );
}

// Props for the dynamic video player
export interface DynamicVideoPlayerProps {
  blueprint?: CompositionBlueprint;
  compositionWidth: number;
  compositionHeight: number;
  backgroundColor?: string;
  playerRef?: React.Ref<PlayerRef>;
  durationInFrames?: number;
  selectedClipId?: string | null;
  onSelectClip?: (clipId: string | null) => void;
  onUpdateTransform?: (clipId: string, transform: Partial<import("../utils/transformUtils").TransformValues>) => void;
}

// The dynamic video player component
export function DynamicVideoPlayer({
  blueprint,
  compositionWidth,
  compositionHeight,
  backgroundColor = "#000000",
  playerRef,
  durationInFrames,
  selectedClipId,
  onSelectClip,
  onUpdateTransform,
}: DynamicVideoPlayerProps) {
  console.log("DynamicVideoPlayer - Blueprint tracks:", blueprint?.length || 0);

  // State for custom video controls
  const [isPlaying, setIsPlaying] = useState(false);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [showControls, setShowControls] = useState(false);
  const [currentFrame, setCurrentFrame] = useState(0);
  
  // Track current frame and playing state continuously
  useEffect(() => {
    if (!playerRef) return;
    
    const interval = setInterval(() => {
      const player = (playerRef as React.RefObject<PlayerRef>)?.current;
      if (player) {
        const frame = player.getCurrentFrame();
        setCurrentFrame(frame);
        
        // Sync isPlaying state with actual player state
        const playing = player.isPlaying();
        if (playing !== isPlaying) {
          setIsPlaying(playing);
        }
      }
    }, 100); // Update every 100ms
    
    return () => clearInterval(interval);
  }, [playerRef, isPlaying]); // Always track, not just when playing

  // Calculate duration based on blueprint
  const calculatedDuration = React.useMemo(() => {
    if (blueprint) {
      return calculateBlueprintDuration(blueprint);
    }
    return durationInFrames || 300; // Default 10 seconds at 30fps
  }, [blueprint, durationInFrames]);

  // Handle play/pause toggle
  const togglePlayPause = () => {
    const player = (playerRef as React.RefObject<PlayerRef>)?.current;
    if (!player) return;
    
    if (isPlaying) {
      player.pause();
      setIsPlaying(false);
    } else {
      player.play();
      setIsPlaying(true);
    }
  };

  // Handle volume change
  const handleVolumeChange = (newVolume: number) => {
    const player = (playerRef as React.RefObject<PlayerRef>)?.current;
    if (!player) return;
    
    setVolume(newVolume);
    player.setVolume(newVolume);
    setIsMuted(newVolume === 0);
  };

  // Handle mute toggle
  const toggleMute = () => {
    const player = (playerRef as React.RefObject<PlayerRef>)?.current;
    if (!player) return;
    
    if (isMuted) {
      player.setVolume(volume);
      setIsMuted(false);
    } else {
      player.setVolume(0);
      setIsMuted(true);
    }
  };

  // Handle fullscreen
  const toggleFullscreen = () => {
    const player = (playerRef as React.RefObject<PlayerRef>)?.current;
    if (!player) return;
    
    player.requestFullscreen();
  };

  return (
    <div className="relative w-full h-full flex flex-col">
      {/* Video Player Container with Overlay */}
      <div className="flex-1 relative overflow-hidden" style={{ pointerEvents: 'none' }}>
        {/* Player - no pointer events so overlay can capture clicks */}
        <div style={{ position: 'absolute', inset: 0, zIndex: 1, pointerEvents: 'none' }}>
          <Player
            ref={playerRef}
            component={DynamicComposition}
            inputProps={{
              blueprint,
              backgroundColor,
            }}
            durationInFrames={Math.max(calculatedDuration, 1)} // Ensure minimum 1 frame
            compositionWidth={compositionWidth}
            compositionHeight={compositionHeight}
            fps={30}
            style={{
              width: "100%",
              height: "100%",
            }}
            // Disable default controls - we're using custom ones
            controls={false}
            showVolumeControls={false}
            allowFullscreen={false}
            clickToPlay={false}
            initiallyShowControls={false}
            // Enable space key for play/pause
            spaceKeyToPlayOrPause={true}
            acknowledgeRemotionLicense
          />
        </div>
        
        {/* Transform Overlay - On top of player */}
        {!isPlaying && blueprint && onSelectClip && onUpdateTransform && (
          <div style={{ position: 'absolute', inset: 0, zIndex: 10, pointerEvents: 'auto' }}>
            <TransformOverlay
              composition={blueprint}
              currentFrame={currentFrame}
              fps={30}
              compositionWidth={compositionWidth}
              compositionHeight={compositionHeight}
              selectedClipId={selectedClipId || null}
              onSelectClip={onSelectClip}
              onUpdateTransform={onUpdateTransform}
              isPlaying={isPlaying}
            />
          </div>
        )}
      </div>

      {/* Custom Controls Bar - Below player, not overlaying */}
      <div 
        className="flex-shrink-0 bg-background border-t border-border"
        style={{ zIndex: 20 }}
      >
        {/* Controls Row */}
        <div className="flex items-center gap-2 px-2 py-1">
          {/* Left side - Volume Control */}
          <div className="flex items-center gap-1.5">
            <button
              onClick={toggleMute}
              className="h-8 w-8 flex items-center justify-center rounded hover:bg-accent transition-colors"
              aria-label={isMuted ? 'Unmute' : 'Mute'}
            >
              {isMuted ? (
                <VolumeX className="w-4 h-4" />
              ) : (
                <Volume2 className="w-4 h-4" />
              )}
            </button>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={isMuted ? 0 : volume}
              onChange={(e) => handleVolumeChange(parseFloat(e.target.value))}
              className="w-20 h-1 bg-border rounded-lg appearance-none cursor-pointer
                [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 
                [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-foreground [&::-webkit-slider-thumb]:cursor-pointer
                [&::-moz-range-thumb]:w-3 [&::-moz-range-thumb]:h-3 [&::-moz-range-thumb]:rounded-full 
                [&::-moz-range-thumb]:bg-foreground [&::-moz-range-thumb]:border-0 [&::-moz-range-thumb]:cursor-pointer"
            />
          </div>

          {/* Center - Play/Pause Button (subtle) */}
          <div className="flex-1 flex justify-center">
            <button
              onClick={togglePlayPause}
              className="h-9 w-9 flex items-center justify-center rounded-full hover:bg-accent transition-colors"
              aria-label={isPlaying ? 'Pause' : 'Play'}
            >
              {isPlaying ? (
                <Pause className="w-4 h-4" fill="currentColor" />
              ) : (
                <Play className="w-4 h-4 ml-0.5" fill="currentColor" />
              )}
            </button>
          </div>

          {/* Right side - Time display and Fullscreen */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground font-mono">
              {Math.floor(currentFrame / 30)}s / {Math.floor(calculatedDuration / 30)}s
            </span>
            <button
              onClick={toggleFullscreen}
              className="h-8 w-8 flex items-center justify-center rounded hover:bg-accent transition-colors"
              aria-label="Fullscreen"
            >
              <Maximize className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
