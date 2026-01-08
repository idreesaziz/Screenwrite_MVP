import { useState, useEffect, useCallback, type RefObject } from "react";
import type { PlayerRef } from "@remotion/player";
import type { CompositionBlueprint, Track, Clip } from "~/composition/BlueprintTypes";

interface PlayerControlsState {
  currentFrame: number;
  timelineFrame: number;
  isPlaying: boolean;
}

interface PlayerControlsActions {
  setTimelineFrame: (frame: number) => void;
  seekTo: (frame: number) => void;
  play: () => void;
  pause: () => void;
  toggle: () => void;
}

const FPS = 30;
const MIN_DURATION_FRAMES = 90; // 3 seconds

export function usePlayerControls(
  playerRef: RefObject<PlayerRef | null>,
  composition: CompositionBlueprint
): [PlayerControlsState, PlayerControlsActions] {
  const [currentFrame, setCurrentFrame] = useState(0);
  const [timelineFrame, setTimelineFrame] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  // Calculate max frame from composition
  const getMaxFrame = useCallback(() => {
    let maxContentFrame = 0;
    for (const track of composition) {
      for (const clip of track.clips) {
        const clipEndFrame = Math.round(clip.endTimeInSeconds * FPS);
        if (clipEndFrame > maxContentFrame) maxContentFrame = clipEndFrame;
      }
    }
    return Math.max(maxContentFrame, MIN_DURATION_FRAMES);
  }, [composition]);

  // Handle timeline frame updates (from scrubber drag)
  const handleTimelineFrameUpdate = useCallback((frame: number) => {
    setTimelineFrame(frame);
    const maxFrame = getMaxFrame();
    if (frame <= maxFrame) {
      setCurrentFrame(frame);
    }
  }, [getMaxFrame]);

  // Player control actions
  const seekTo = useCallback((frame: number) => {
    playerRef.current?.seekTo(frame);
  }, [playerRef]);

  const play = useCallback(() => {
    playerRef.current?.play();
  }, [playerRef]);

  const pause = useCallback(() => {
    playerRef.current?.pause();
  }, [playerRef]);

  const toggle = useCallback(() => {
    const player = playerRef.current;
    if (player) {
      if (player.isPlaying()) {
        player.pause();
      } else {
        player.play();
      }
    }
  }, [playerRef]);

  // Setup player event listeners
  useEffect(() => {
    const setupPlayerListeners = () => {
      const player = playerRef.current;
      if (!player) {
        setTimeout(setupPlayerListeners, 100);
        return;
      }

      setCurrentFrame(player.getCurrentFrame());

      const handleFrameUpdate = (event: { detail: { frame: number } }) => {
        setCurrentFrame(event.detail.frame);
        setTimelineFrame(event.detail.frame);
      };

      const handleSeeked = (event: { detail: { frame: number } }) => {
        setCurrentFrame(event.detail.frame);
        setTimelineFrame(event.detail.frame);
      };

      const handlePlay = () => setIsPlaying(true);
      const handlePause = () => setIsPlaying(false);

      player.addEventListener("frameupdate", handleFrameUpdate);
      player.addEventListener("seeked", handleSeeked);
      player.addEventListener("play", handlePlay);
      player.addEventListener("pause", handlePause);

      // Polling for smooth scrubber movement
      const interval = setInterval(() => {
        const frame = player.getCurrentFrame();
        setCurrentFrame(frame);
        setTimelineFrame(frame);
      }, 16);

      return () => {
        player.removeEventListener("frameupdate", handleFrameUpdate);
        player.removeEventListener("seeked", handleSeeked);
        player.removeEventListener("play", handlePlay);
        player.removeEventListener("pause", handlePause);
        clearInterval(interval);
      };
    };

    const cleanup = setupPlayerListeners();
    return cleanup || (() => {});
  }, [playerRef]);

  // Global spacebar play/pause
  useEffect(() => {
    const handleKeyPress = (event: KeyboardEvent) => {
      if (event.code !== "Space") return;

      const target = event.target as HTMLElement;
      const isInputElement =
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.contentEditable === "true" ||
        target.isContentEditable;

      if (isInputElement) return;

      event.preventDefault();
      toggle();
    };

    document.addEventListener("keydown", handleKeyPress);
    return () => document.removeEventListener("keydown", handleKeyPress);
  }, [toggle]);

  return [
    { currentFrame, timelineFrame, isPlaying },
    {
      setTimelineFrame: handleTimelineFrameUpdate,
      seekTo,
      play,
      pause,
      toggle
    }
  ];
}
