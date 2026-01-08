import { useCallback } from "react";
import { toast } from "sonner";
import { useUndoRedo } from "./useUndoRedo";
import { emptyCompositionBlueprint, ensureMinimumTracks } from "~/composition";
import { updateClipTransform, type TransformValues } from "~/lib/transformUtils";
import type { CompositionBlueprint, Track, Clip } from "~/composition";
import type { MediaBinItem } from "~/components/editor/timeline/types";

export interface CompositionEditorActions {
  set: (composition: CompositionBlueprint) => void;
  undo: () => void;
  redo: () => void;
  canUndo: boolean;
  canRedo: boolean;
  dropMedia: (mediaItem: MediaBinItem, trackIndex: number, timeInSeconds: number) => void;
  moveClip: (clipId: string, newTrackIndex: number, newStartTime: number) => void;
  splitClip: (clipId: string, splitTimeInSeconds: number) => void;
  deleteClip: (clipId: string) => void;
  updateClipTransform: (clipId: string, transform: Partial<TransformValues>) => void;
  updateClipElements: (clipId: string, newElements: string[]) => void;
  ensureMinimumTracks: (count: number) => void;
  reset: () => void;
}

export function useCompositionEditor(): [CompositionBlueprint, CompositionEditorActions] {
  const [composition, undoRedoActions] = useUndoRedo<CompositionBlueprint>(emptyCompositionBlueprint);

  const findClip = useCallback((clipId: string): { clip: Clip; trackIndex: number } | null => {
    for (let trackIdx = 0; trackIdx < composition.length; trackIdx++) {
      const clip = composition[trackIdx].clips.find((c: Clip) => c.id === clipId);
      if (clip) {
        return { clip, trackIndex: trackIdx };
      }
    }
    return null;
  }, [composition]);

  const checkOverlap = useCallback((
    trackIndex: number,
    startTime: number,
    endTime: number,
    excludeClipId?: string
  ): boolean => {
    const track = composition[trackIndex];
    if (!track) return false;
    
    return track.clips.some((clip: Clip) => {
      if (excludeClipId && clip.id === excludeClipId) return false;
      return !(endTime <= clip.startTimeInSeconds || startTime >= clip.endTimeInSeconds);
    });
  }, [composition]);

  const dropMedia = useCallback((
    mediaItem: MediaBinItem,
    trackIndex: number,
    timeInSeconds: number
  ) => {
    const clipDuration = mediaItem.mediaType === "image" ? 3 : mediaItem.durationInSeconds;
    const endTime = timeInSeconds + clipDuration;

    if (checkOverlap(trackIndex, timeInSeconds, endTime)) {
      toast.error(`Cannot add ${mediaItem.name}: would overlap with existing clip on track ${trackIndex + 1}`);
      return;
    }

    let elements: string[] = [];
    const timestamp = Date.now();

    if (mediaItem.mediaType === "video") {
      elements = [
        `Video;id:video-${timestamp};parent:root;src:${mediaItem.mediaUrlLocal || mediaItem.mediaUrlRemote};width:100%;height:100%;muted:true;style:objectFit:cover`
      ];
    } else if (mediaItem.mediaType === "image") {
      elements = [
        `Img;id:image-${timestamp};parent:root;src:${mediaItem.mediaUrlLocal || mediaItem.mediaUrlRemote};width:100%;height:100%;style:objectFit:cover`
      ];
    } else if (mediaItem.mediaType === "text") {
      const { fontSize = 48, fontFamily = "Arial", color = "#ffffff", fontWeight = "normal", textAlign = "center", textContent = "Text" } = mediaItem.text || {};
      elements = [
        `div;id:text-container-${timestamp};parent:root;width:100%;height:100%;display:flex;alignItems:center;justifyContent:center;fontSize:${fontSize}px;fontFamily:${fontFamily};color:${color};fontWeight:${fontWeight};textAlign:${textAlign};text:${textContent}`
      ];
    }

    const newClip: Clip = {
      id: `dropped-${mediaItem.id}-${Date.now()}`,
      startTimeInSeconds: timeInSeconds,
      endTimeInSeconds: endTime,
      element: { elements }
    };

    const updated = [...composition];
    while (updated.length <= trackIndex) {
      updated.push({ clips: [] });
    }
    updated[trackIndex] = {
      ...updated[trackIndex],
      clips: [...updated[trackIndex].clips, newClip]
    };

    undoRedoActions.set(updated);
    toast.success(`Added ${mediaItem.name} to track ${trackIndex + 1}`);
  }, [composition, checkOverlap, undoRedoActions]);

  const moveClip = useCallback((
    clipId: string,
    newTrackIndex: number,
    newStartTime: number
  ) => {
    const found = findClip(clipId);
    if (!found) {
      toast.error("Clip not found");
      return;
    }

    const { clip, trackIndex: sourceTrackIndex } = found;
    const clipDuration = clip.endTimeInSeconds - clip.startTimeInSeconds;
    const newEndTime = newStartTime + clipDuration;

    if (checkOverlap(newTrackIndex, newStartTime, newEndTime, clipId)) {
      toast.error(`Cannot move clip: would overlap with existing clip on track ${newTrackIndex + 1}`);
      return;
    }

    const updated = [...composition];
    while (updated.length <= newTrackIndex) {
      updated.push({ clips: [] });
    }

    updated[sourceTrackIndex] = {
      ...updated[sourceTrackIndex],
      clips: updated[sourceTrackIndex].clips.filter((c: Clip) => c.id !== clipId)
    };

    const movedClip: Clip = {
      ...clip,
      startTimeInSeconds: newStartTime,
      endTimeInSeconds: newEndTime
    };

    updated[newTrackIndex] = {
      ...updated[newTrackIndex],
      clips: [...updated[newTrackIndex].clips, movedClip]
    };

    undoRedoActions.set(updated);
    toast.success(`Moved clip to track ${newTrackIndex + 1}`);
  }, [composition, findClip, checkOverlap, undoRedoActions]);

  const splitClip = useCallback((clipId: string, splitTimeInSeconds: number) => {
    const found = findClip(clipId);
    if (!found) {
      toast.error("Clip not found");
      return;
    }

    const { clip, trackIndex } = found;

    if (splitTimeInSeconds <= clip.startTimeInSeconds || splitTimeInSeconds >= clip.endTimeInSeconds) {
      toast.error("Split time must be within the clip duration");
      return;
    }

    const leftClip: Clip = {
      ...clip,
      id: `${clip.id}:L`,
      endTimeInSeconds: splitTimeInSeconds
    };

    const rightClip: Clip = {
      ...clip,
      id: `${clip.id}:R`,
      startTimeInSeconds: splitTimeInSeconds
    };

    const updated = [...composition];
    updated[trackIndex] = {
      ...updated[trackIndex],
      clips: updated[trackIndex].clips
        .map((c: Clip) => (c.id === clipId ? leftClip : c))
        .concat([rightClip])
    };

    undoRedoActions.set(updated);
    toast.success("Split clip into two parts");
  }, [composition, findClip, undoRedoActions]);

  const deleteClip = useCallback((clipId: string) => {
    const found = findClip(clipId);
    if (!found) {
      toast.error("Clip not found");
      return;
    }

    const { trackIndex } = found;
    const updated = [...composition];
    updated[trackIndex] = {
      ...updated[trackIndex],
      clips: updated[trackIndex].clips.filter((c: Clip) => c.id !== clipId)
    };

    undoRedoActions.set(updated);
    toast.success("Deleted clip");
  }, [composition, findClip, undoRedoActions]);

  const handleUpdateClipTransform = useCallback((
    clipId: string,
    transform: Partial<TransformValues>
  ) => {
    const updated = composition.map((track: Track) => ({
      ...track,
      clips: track.clips.map((clip: Clip) => {
        if (clip.id === clipId) {
          return updateClipTransform(clip, transform);
        }
        return clip;
      })
    }));
    undoRedoActions.set(updated);
  }, [composition, undoRedoActions]);

  const handleUpdateClipElements = useCallback((clipId: string, newElements: string[]) => {
    const updated = composition.map((track: Track) => ({
      ...track,
      clips: track.clips.map((clip: Clip) =>
        clip.id === clipId
          ? { ...clip, element: { elements: newElements } }
          : clip
      )
    }));
    undoRedoActions.set(updated);
  }, [composition, undoRedoActions]);

  const handleEnsureMinimumTracks = useCallback((count: number) => {
    const updated = ensureMinimumTracks(composition, count);
    if (updated.length !== composition.length) {
      undoRedoActions.set(updated);
    }
  }, [composition, undoRedoActions]);

  const reset = useCallback(() => {
    undoRedoActions.set(emptyCompositionBlueprint);
  }, [undoRedoActions]);

  return [
    composition,
    {
      set: undoRedoActions.set,
      undo: undoRedoActions.undo,
      redo: undoRedoActions.redo,
      canUndo: undoRedoActions.canUndo,
      canRedo: undoRedoActions.canRedo,
      dropMedia,
      moveClip,
      splitClip,
      deleteClip,
      updateClipTransform: handleUpdateClipTransform,
      updateClipElements: handleUpdateClipElements,
      ensureMinimumTracks: handleEnsureMinimumTracks,
      reset
    }
  ];
}
