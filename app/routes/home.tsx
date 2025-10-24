import React, { useRef, useEffect, useCallback, useState } from "react";
import type { PlayerRef } from "@remotion/player";
import axios from "axios";
import { apiUrl } from "~/utils/api";
import {
  Upload,
  ChevronLeft,
  Undo2,
  Redo2,
  LogOut,
} from "lucide-react";

// Components
import LeftPanel from "~/components/editor/LeftPanel";
import { DynamicVideoPlayer } from "~/video-compositions/DynamicComposition";
import { calculateBlueprintDuration } from "~/video-compositions/executeClipElement";
import { emptyCompositionBlueprint, ensureMinimumTracks } from "~/video-compositions/EmptyComposition";
import type { CompositionBlueprint } from "~/video-compositions/BlueprintTypes";
import { RenderStatus } from "~/components/timeline/RenderStatus";
import { Button } from "~/components/ui/button";
import { Badge } from "~/components/ui/badge";
import { Separator } from "~/components/ui/separator";
import { Switch } from "~/components/ui/switch";
import { Label } from "~/components/ui/label";
import { Input } from "~/components/ui/input";
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "~/components/ui/resizable";
import { toast } from "sonner";

// Hooks
import { useMediaBin } from "~/hooks/useMediaBin";
import { useRenderer } from "~/hooks/useRenderer";
import { useUndoRedo, useUndoRedoShortcuts } from "~/hooks/useUndoRedo";

// Transform utilities
import { updateClipTransform, type TransformValues } from "../utils/transformUtils";
import { useAuth } from "~/hooks/useAuth";


// Types and constants
import { type Transition, type MediaBinItem } from "~/components/timeline/types";
import { useNavigate } from "react-router";

// Custom Timeline
import TimelineView from "../components/custom-timeline/TimelineView"; // direct relative path to bust alias cache
import { ChatBox } from "~/components/chat/ChatBox";
import { ProviderPairingModal } from "~/components/chat/ProviderPairingModal";

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
}

export default function TimelineEditor() {
  const containerRef = useRef<HTMLDivElement>(null);
  const playerRef = useRef<PlayerRef>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { signOut, user, getToken } = useAuth();

  const navigate = useNavigate();

  const [width, setWidth] = useState<number>(1920);
  const [height, setHeight] = useState<number>(1080);
  const [isAutoSize, setIsAutoSize] = useState<boolean>(false);
  const [isChatMinimized, setIsChatMinimized] = useState<boolean>(true);
  
  // Provider pairing state
  const [showProviderModal, setShowProviderModal] = useState<boolean>(true);
  const [selectedEditProvider, setSelectedEditProvider] = useState<"gemini" | "claude">("gemini");
  const [selectedAgentProvider, setSelectedAgentProvider] = useState<"gemini" | "claude" | "openai">("gemini");
  
  const handleProviderPairingSelect = (
    editProvider: "gemini" | "claude",
    agentProvider: "gemini" | "claude" | "openai"
  ) => {
    setSelectedEditProvider(editProvider);
    setSelectedAgentProvider(agentProvider);
    setShowProviderModal(false);
  };

  // Video playback state
  const [durationInFrames, setDurationInFrames] = useState<number>(90); // Start with 3 seconds (90 frames at 30fps) for empty composition

  // AI generation state with undo/redo
  const [currentComposition, undoRedoActions] = useUndoRedo<CompositionBlueprint>(emptyCompositionBlueprint);
  
  // Clip selection state for transform overlay
  const [selectedClipId, setSelectedClipId] = useState<string | null>(null);
  
  // Handler to update clip transform
  const handleUpdateClipTransform = (clipId: string, transform: Partial<TransformValues>) => {
    console.log('handleUpdateClipTransform called:', clipId, transform);
    
    const newComposition = currentComposition.map(track => ({
      ...track,
      clips: track.clips.map(clip => {
        if (clip.id === clipId) {
          const updatedClip = updateClipTransform(clip, transform);
          console.log('Updated clip:', updatedClip.element.elements);
          return updatedClip;
        }
        return clip;
      })
    }));
    
    console.log('Setting new composition');
    undoRedoActions.set(newComposition, "Transform clip");
  };

  // Handler to update clip elements (from properties panel)
  const handleUpdateClipElements = (clipId: string, newElements: string[]) => {
    const newComposition = currentComposition.map(track => ({
      ...track,
      clips: track.clips.map(clip =>
        clip.id === clipId
          ? { ...clip, element: { elements: newElements } }
          : clip
      )
    }));
    undoRedoActions.set(newComposition, "Update clip properties");
  };
  
  // Setup keyboard shortcuts for undo/redo
  const handleUndoRedoKeyDown = useUndoRedoShortcuts(undoRedoActions);
  
  // Add keyboard event listener
  useEffect(() => {
    document.addEventListener('keydown', handleUndoRedoKeyDown);
    return () => document.removeEventListener('keydown', handleUndoRedoKeyDown);
  }, [handleUndoRedoKeyDown]);
  
  const [isAiGenerating, setIsAiGenerating] = useState(false);
  
  // Helper to check if we have generated content (more than empty composition)
  const hasGeneratedContent = currentComposition.some(track => track.clips.length > 0);

  // Handle dropping media from library onto timeline
  const handleDropMediaOnTimeline = (mediaItem: MediaBinItem, trackIndex: number, timeInSeconds: number) => {
    console.log('Adding media to timeline:', mediaItem.name, 'track:', trackIndex, 'time:', timeInSeconds);
    
    // Calculate clip duration (default to 3 seconds for images)
    const clipDuration = mediaItem.mediaType === 'image' ? 3 : mediaItem.durationInSeconds;
    const endTime = timeInSeconds + clipDuration;
    
    // Check for overlaps on the target track
    const targetTrack = currentComposition[trackIndex];
    if (targetTrack) {
      const hasOverlap = targetTrack.clips.some(clip => {
        // Check if new clip would overlap with existing clip
        return !(endTime <= clip.startTimeInSeconds || timeInSeconds >= clip.endTimeInSeconds);
      });
      
      if (hasOverlap) {
        toast.error(`Cannot add ${mediaItem.name}: would overlap with existing clip on track ${trackIndex + 1}`);
        return; // Prevent the drop
      }
    }
    
    // Generate element strings based on media type
    let elements: string[] = [];
    const timestamp = Date.now();
    
    if (mediaItem.mediaType === 'video') {
      elements = [
        `Video;id:video-${timestamp};parent:root;src:${mediaItem.mediaUrlLocal || mediaItem.mediaUrlRemote};width:100%;height:100%;muted:true;style:objectFit:cover`
      ];
    } else if (mediaItem.mediaType === 'image') {
      elements = [
        `Img;id:image-${timestamp};parent:root;src:${mediaItem.mediaUrlLocal || mediaItem.mediaUrlRemote};width:100%;height:100%;style:objectFit:cover`
      ];
    } else if (mediaItem.mediaType === 'text') {
      const fontSize = mediaItem.text?.fontSize || 48;
      const fontFamily = mediaItem.text?.fontFamily || 'Arial';
      const color = mediaItem.text?.color || '#ffffff';
      const fontWeight = mediaItem.text?.fontWeight || 'normal';
      const textAlign = mediaItem.text?.textAlign || 'center';
      const textContent = mediaItem.text?.textContent || 'Text';
      
      elements = [
        `div;id:text-container-${timestamp};parent:root;width:100%;height:100%;display:flex;alignItems:center;justifyContent:center;fontSize:${fontSize}px;fontFamily:${fontFamily};color:${color};fontWeight:${fontWeight};textAlign:${textAlign};text:${textContent}`
      ];
    }
    
    // Create new clip
    const newClip = {
      id: `dropped-${mediaItem.id}-${Date.now()}`,
      startTimeInSeconds: timeInSeconds,
      endTimeInSeconds: endTime,
      element: {
        elements: elements
      }
    };
    
    // Create updated composition
    const updatedComposition = [...currentComposition];
    
    // Ensure we have enough tracks
    while (updatedComposition.length <= trackIndex) {
      updatedComposition.push({ clips: [] });
    }
    
    // Add the new clip to the specified track
    updatedComposition[trackIndex] = {
      ...updatedComposition[trackIndex],
      clips: [...updatedComposition[trackIndex].clips, newClip]
    };
    
    // Update the composition with undo support
    undoRedoActions.set(updatedComposition, `Add ${mediaItem.name} to track ${trackIndex + 1}`);
    
    toast.success(`Added ${mediaItem.name} to track ${trackIndex + 1}`);
  };

  // Handle moving clips within the timeline
  const handleMoveClip = (clipId: string, newTrackIndex: number, newStartTime: number) => {
    console.log('Moving clip:', clipId, 'to track:', newTrackIndex, 'time:', newStartTime);
    
    // Find the clip in the current composition
    let sourceClip = null;
    let sourceTrackIndex = -1;
    let sourceClipIndex = -1;
    
    for (let trackIdx = 0; trackIdx < currentComposition.length; trackIdx++) {
      const clipIdx = currentComposition[trackIdx].clips.findIndex(clip => clip.id === clipId);
      if (clipIdx !== -1) {
        sourceClip = currentComposition[trackIdx].clips[clipIdx];
        sourceTrackIndex = trackIdx;
        sourceClipIndex = clipIdx;
        break;
      }
    }
    
    if (!sourceClip) {
      toast.error('Clip not found');
      return;
    }
    
    // Calculate new clip times
    const clipDuration = sourceClip.endTimeInSeconds - sourceClip.startTimeInSeconds;
    const newEndTime = newStartTime + clipDuration;
    
    // Check for overlaps on the target track (exclude the clip being moved)
    const targetTrack = currentComposition[newTrackIndex];
    if (targetTrack) {
      const hasOverlap = targetTrack.clips.some(clip => {
        if (clip.id === clipId) return false; // Don't check against itself
        return !(newEndTime <= clip.startTimeInSeconds || newStartTime >= clip.endTimeInSeconds);
      });
      
      if (hasOverlap) {
        toast.error(`Cannot move clip: would overlap with existing clip on track ${newTrackIndex + 1}`);
        return;
      }
    }
    
    // Create updated composition
    const updatedComposition = [...currentComposition];
    
    // Ensure we have enough tracks
    while (updatedComposition.length <= newTrackIndex) {
      updatedComposition.push({ clips: [] });
    }
    
    // Remove clip from source track
    updatedComposition[sourceTrackIndex] = {
      ...updatedComposition[sourceTrackIndex],
      clips: updatedComposition[sourceTrackIndex].clips.filter(clip => clip.id !== clipId)
    };
    
    // Add clip to target track with new timing
    const movedClip = {
      ...sourceClip,
      startTimeInSeconds: newStartTime,
      endTimeInSeconds: newEndTime
    };
    
    updatedComposition[newTrackIndex] = {
      ...updatedComposition[newTrackIndex],
      clips: [...updatedComposition[newTrackIndex].clips, movedClip]
    };
    
    // Update the composition with undo support
    undoRedoActions.set(updatedComposition, `Move clip to track ${newTrackIndex + 1}`);
    
    toast.success(`Moved clip to track ${newTrackIndex + 1}`);
  };

  // Handle splitting clips at a specific time
  const handleSplitClip = (clipId: string, splitTimeInSeconds: number) => {
    console.log('Splitting clip:', clipId, 'at time:', splitTimeInSeconds);
    
    // Find the clip to split
    let sourceClip = null;
    let sourceTrackIndex = -1;
    
    for (let trackIdx = 0; trackIdx < currentComposition.length; trackIdx++) {
      const clipIdx = currentComposition[trackIdx].clips.findIndex(clip => clip.id === clipId);
      if (clipIdx !== -1) {
        sourceClip = currentComposition[trackIdx].clips[clipIdx];
        sourceTrackIndex = trackIdx;
        break;
      }
    }
    
    if (!sourceClip || sourceTrackIndex === -1) {
      toast.error('Clip not found');
      return;
    }
    
    // Check if split time is within the clip bounds
    if (splitTimeInSeconds <= sourceClip.startTimeInSeconds || splitTimeInSeconds >= sourceClip.endTimeInSeconds) {
      toast.error('Split time must be within the clip duration');
      return;
    }
    
    // Create two new clips
    const leftClip = {
      ...sourceClip,
      id: `${sourceClip.id}:L`,
      endTimeInSeconds: splitTimeInSeconds
    };
    
    const rightClip = {
      ...sourceClip,
      id: `${sourceClip.id}:R`,
      startTimeInSeconds: splitTimeInSeconds
    };
    
    // Create updated composition
    const updatedComposition = [...currentComposition];
    
    // Replace the original clip with the two new clips
    updatedComposition[sourceTrackIndex] = {
      ...updatedComposition[sourceTrackIndex],
      clips: updatedComposition[sourceTrackIndex].clips.map(clip => 
        clip.id === clipId ? leftClip : clip
      ).concat([rightClip])
    };
    
    // Update the composition with undo support
    undoRedoActions.set(updatedComposition, `Split clip into two parts`);
    
    toast.success(`Split clip into two parts`);
  };

  // Handle deleting clips
  const handleDeleteClip = (clipId: string) => {
    console.log('Deleting clip:', clipId);
    
    // Find the clip to delete
    let sourceTrackIndex = -1;
    
    for (let trackIdx = 0; trackIdx < currentComposition.length; trackIdx++) {
      const clipExists = currentComposition[trackIdx].clips.some(clip => clip.id === clipId);
      if (clipExists) {
        sourceTrackIndex = trackIdx;
        break;
      }
    }
    
    if (sourceTrackIndex === -1) {
      toast.error('Clip not found');
      return;
    }
    
    // Create updated composition
    const updatedComposition = [...currentComposition];
    
    // Remove the clip
    updatedComposition[sourceTrackIndex] = {
      ...updatedComposition[sourceTrackIndex],
      clips: updatedComposition[sourceTrackIndex].clips.filter(clip => clip.id !== clipId)
    };
    
    // Update the composition with undo support
    undoRedoActions.set(updatedComposition, `Delete clip`);
    
    toast.success(`Deleted clip`);
  };

  // Custom frame update handler that allows timeline to move freely
  const handleTimelineFrameUpdate = (frame: number) => {
    setTimelineFrame(frame);
    // Only update currentFrame if we're within content bounds, otherwise let player events handle it
    if (playerRef?.current) {
      // Calculate max frame based on current composition
      let maxContentFrame = 0;
      for (const track of currentComposition) {
        for (const clip of track.clips) {
          const clipEndFrame = Math.round(clip.endTimeInSeconds * 30); // 30 fps
          if (clipEndFrame > maxContentFrame) maxContentFrame = clipEndFrame;
        }
      }
      const maxFrame = Math.max(maxContentFrame, 90); // Minimum 3 seconds
      
      if (frame <= maxFrame) {
        setCurrentFrame(frame);
      }
    }
  };

  const [chatMessages, setChatMessages] = useState<Message[]>([]);
  const [mounted, setMounted] = useState(false)

  // video player media selection state
  const [selectedItem, setSelectedItem] = useState<string | null>(null);
  
  // Video playback state for scrubber
  const [currentFrame, setCurrentFrame] = useState<number>(0);
  const [timelineFrame, setTimelineFrame] = useState<number>(0); // Separate frame for timeline scrubber position



  const {
    mediaBinItems,
    handleAddMediaToBin,
    handleAddTextToBin,
    handleAddDirectMediaBinItem,
    handleUpdateMediaItem,
    contextMenu,
    handleContextMenu,
    handleDeleteFromContext,
    handleSplitAudioFromContext,
    handleCloseContextMenu
  } = useMediaBin(() => {}, getToken); // Pass getToken for authenticated GCS uploads

  const { isRendering, renderStatus, handleRenderVideo } = useRenderer();

  // Blueprint-only state (no more TSX execution)
  const [previewSettings] = useState({
    width: 1920,
    height: 1080,
    backgroundColor: "#000000",
    fps: 30,
  });

  // TODO: Add blueprint generation logic here when connecting AI

  // Event handlers
  const handleAddMediaClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleFileInputChange = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        const fileArray = Array.from(files);
        let successCount = 0;
        let errorCount = 0;

        // Process files sequentially to avoid overwhelming the system
        for (const file of fileArray) {
          try {
            await handleAddMediaToBin(file);
            successCount++;
          } catch (error) {
            errorCount++;
            console.error(`Failed to add ${file.name}:`, error);
          }
        }

        if (successCount > 0 && errorCount > 0) {
          toast.warning(`Imported ${successCount} file${successCount > 1 ? 's' : ''}, ${errorCount} failed`);
        } else if (errorCount > 0) {
          toast.error(`Failed to import ${errorCount} file${errorCount > 1 ? 's' : ''}`);
        }

        e.target.value = "";
      }
    },
    [handleAddMediaToBin]
  );

  const handleAutoSizeChange = useCallback((auto: boolean) => {
    setIsAutoSize(auto);
  }, []);

  // Update duration when composition changes
  useEffect(() => {
    // Calculate duration from current composition
    if (currentComposition && currentComposition.length > 0) {
      const calculatedDuration = calculateBlueprintDuration(currentComposition);
      // Ensure minimum duration of 1 frame (30fps = 1 frame minimum)
      setDurationInFrames(Math.max(calculatedDuration, 1));
    } else {
      // Empty composition gets a default 3-second duration (90 frames at 30fps)
      setDurationInFrames(90);
    }
  }, [currentComposition]);

  // Update current frame for scrubber using player events + fallback polling
  useEffect(() => {
    const setupPlayerListeners = () => {
      const player = playerRef.current;
      if (!player) {
        // Retry after a short delay if player isn't ready yet
        setTimeout(setupPlayerListeners, 100);
        return;
      }

      // Get initial frame position
      setCurrentFrame(player.getCurrentFrame());

      const handleFrameUpdate = (event: { detail: { frame: number } }) => {
        setCurrentFrame(event.detail.frame);
        setTimelineFrame(event.detail.frame); // Keep timeline in sync when player updates
      };

      const handleSeeked = (event: { detail: { frame: number } }) => {
        setCurrentFrame(event.detail.frame);
        setTimelineFrame(event.detail.frame); // Keep timeline in sync when seeking
      };

      // Listen to the player's frame updates for real-time position
      player.addEventListener('frameupdate', handleFrameUpdate);
      player.addEventListener('seeked', handleSeeked);

      // Continuous polling for smooth scrubber movement during playback
      const interval = setInterval(() => {
        const currentPlayerFrame = player.getCurrentFrame();
        setCurrentFrame(currentPlayerFrame);
        setTimelineFrame(currentPlayerFrame); // Keep timeline in sync during playback
      }, 16); // 60fps polling for smooth scrubber movement

      // Return cleanup function
      return () => {
        player.removeEventListener('frameupdate', handleFrameUpdate);
        player.removeEventListener('seeked', handleSeeked);
        clearInterval(interval);
      };
    };

    const cleanup = setupPlayerListeners();

    // Return the cleanup function or a no-op if setupPlayerListeners returned undefined
    return cleanup || (() => {});
  }, []);

  // Global spacebar play/pause functionality - like original
  useEffect(() => {
    const handleGlobalKeyPress = (event: KeyboardEvent) => {
      // Only handle spacebar when not focused on input elements
      if (event.code === "Space") {
        const target = event.target as HTMLElement;
        const isInputElement =
          target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          target.contentEditable === "true" ||
          target.isContentEditable;

        // If user is typing in an input field, don't interfere
        if (isInputElement) {
          return;
        }

        // Prevent spacebar from scrolling the page
        event.preventDefault();

        const player = playerRef.current;
        if (player) {
          if (player.isPlaying()) {
            player.pause();
          } else {
            player.play();
          }
        }
      }
    };

    // Add event listener to document for global capture
    document.addEventListener("keydown", handleGlobalKeyPress);

    return () => {
      document.removeEventListener("keydown", handleGlobalKeyPress);
    };
  }, []); // Empty dependency array since we're accessing playerRef.current directly

  // AI Composition Generation Function
  const handleGenerateComposition = useCallback(async (
    userRequest: string, 
    mediaBinItems: MediaBinItem[], 
    modelType: string = "gemini",
    provider: string = "gemini"
  ): Promise<boolean> => {
    // DEBUG: Log incoming parameters
    console.log("🔍 DEBUG handleGenerateComposition: modelType =", modelType, "provider =", provider);
    
    // Map frontend model names to backend model names
    const modelNameMap: Record<string, string> = {
      "gemini": "gemini-2.5-flash",
      "openai": "gpt-4o-mini"
    };
    
    const backendModelName = modelNameMap[modelType] || modelType;
    
    console.log("🤖 AI Generation: Starting composition generation for:", userRequest, "using model:", backendModelName);
    setIsAiGenerating(true);
    
    try {
      // Get authentication token
      const token = await getToken();
      if (!token) {
        console.error("🤖 AI Generation: No authentication token available");
        toast.error("Authentication required. Please sign in.");
        return false;
      }
      
      // Call the Python backend API with current composition
      const response = await axios.post(apiUrl("/api/v1/compositions/generate", true), {
        user_request: userRequest,
        preview_settings: previewSettings,
        media_library: mediaBinItems.map(item => ({
          id: item.id,
          name: item.name,
          mediaType: item.mediaType,
          durationInSeconds: item.durationInSeconds,
          media_width: item.media_width,
          media_height: item.media_height,
          mediaUrlLocal: item.mediaUrlLocal,
          mediaUrlRemote: item.mediaUrlRemote,
        })),
        current_composition: currentComposition, // Send current composition for incremental editing
        preview_frame: null,
        model_name: backendModelName, // Use mapped model name
        provider: provider, // Send selected provider
      }, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      console.log("🔍 DEBUG: API request payload provider =", provider);
      console.log("🤖 AI Generation: Received response:", response.data);

      if (response.data.success && response.data.composition_code) {
        try {
          // Parse the JSON response as CompositionBlueprint
          const blueprintJson = JSON.parse(response.data.composition_code);
          console.log("🤖 AI Generation: Parsed blueprint:", blueprintJson);

          // Ensure the blueprint has proper structure and minimum tracks
          const validBlueprint = ensureMinimumTracks(Array.isArray(blueprintJson) ? blueprintJson : [], 4);

          // Set the updated composition as active with undo support
          undoRedoActions.set(validBlueprint, `AI generated composition: "${userRequest}"`);
          
          // Calculate and set duration with minimum safety
          const calculatedDuration = calculateBlueprintDuration(validBlueprint);
          const safeDuration = Math.max(calculatedDuration, 90); // Minimum 3 seconds
          setDurationInFrames(safeDuration);

          console.log("🤖 AI Generation: Blueprint applied successfully, duration:", safeDuration);
          toast.success("🎬 AI composition generated successfully!");
          return true;
        } catch (parseError) {
          console.error("🤖 AI Generation: JSON parse error:", parseError);
          toast.error("Failed to parse AI response");
          return false;
        }
      } else {
        console.error("🤖 AI Generation: API returned error:", response.data.error_message);
        toast.error(response.data.error_message || "Failed to generate composition");
        return false;
      }
    } catch (error) {
      console.error("🤖 AI Generation: Network error:", error);
      toast.error("Failed to connect to AI service");
      return false;
    } finally {
      setIsAiGenerating(false);
    }
  }, [previewSettings, currentComposition, getToken]);

  // Handle adding generated images to media bin
  const handleAddGeneratedImage = useCallback(async (item: MediaBinItem): Promise<void> => {
    console.log("🎨 Adding generated image to media bin:", item);
    handleAddDirectMediaBinItem(item);
  }, [handleAddDirectMediaBinItem]);

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) return null;

  return (
    <div className="h-screen flex flex-col bg-background text-foreground" onPointerDown={(e: React.PointerEvent) => {
      if (e.button !== 0) {
        return;
      }
      setSelectedItem(null);
    }}>
      {/* Ultra-minimal Top Bar */}
      <header className="h-9 border-b border-border/50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 flex items-center justify-between px-3 shrink-0">
        <div className="flex items-center gap-3">
          <h1 className="text-sm font-medium tracking-tight">Screenwrite</h1>
        </div>

        <div className="flex items-center gap-1">
          {/* User Info */}
          {user && (
            <span className="text-xs text-muted-foreground px-2">
              {user.email}
            </span>
          )}
          
          {/* Sign Out */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => signOut()}
            className="h-7 w-7 p-0 hover:bg-muted"
            title="Sign Out"
          >
            <LogOut className="h-3.5 w-3.5" />
          </Button>
        </div>
      </header>

      {/* Main content area with chat extending to bottom */}
      <ResizablePanelGroup direction="horizontal" className="flex-1">
        {/* Left section with media bin, video preview, and timeline */}
        <ResizablePanel defaultSize={isChatMinimized ? 100 : 80}>
          <ResizablePanelGroup direction="vertical">
            {/* Top section with media bin and video preview */}
            <ResizablePanel defaultSize={65} minSize={40}>
              <ResizablePanelGroup direction="horizontal">
                {/* Left Panel - Media Bin & Tools */}
                <ResizablePanel defaultSize={25} minSize={15} maxSize={40}>
                  <div className="h-full border-r border-border">
                    <LeftPanel
                      mediaBinItems={mediaBinItems}
                      onAddMedia={handleAddMediaToBin}
                      onAddText={handleAddTextToBin}
                      onAddMediaClick={handleAddMediaClick}
                      contextMenu={contextMenu}
                      handleContextMenu={handleContextMenu}
                      handleDeleteFromContext={handleDeleteFromContext}
                      handleSplitAudioFromContext={handleSplitAudioFromContext}
                      handleCloseContextMenu={handleCloseContextMenu}
                      selectedClipId={selectedClipId}
                      currentComposition={currentComposition}
                      onUpdateClipElements={handleUpdateClipElements}
                    />
                  </div>
                </ResizablePanel>

                <ResizableHandle withHandle />

                {/* Video Preview Area */}
                <ResizablePanel defaultSize={75}>
                  <div className="h-full flex flex-col bg-background">
                    {/* Compact Top Bar */}
                    <div className="h-8 border-b border-border/50 bg-muted/30 flex items-center justify-between px-3 shrink-0">
                      <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                        <span>Resolution:</span>
                        <div className="flex items-center gap-1">
                          <Input
                            type="number"
                            value={width}
                            onChange={(e) =>
                              setWidth(Number(e.target.value))
                            }
                            className="h-5 w-14 text-xs px-1 border-0 bg-muted/50"
                          />
                          <span>×</span>
                          <Input
                            type="number"
                            value={height}
                            onChange={(e) =>
                              setHeight(Number(e.target.value))
                            }
                            className="h-5 w-14 text-xs px-1 border-0 bg-muted/50"
                          />
                        </div>
                      </div>

                      <div className="flex items-center gap-1">
                        {/* Show chat toggle when minimized */}
                        {isChatMinimized && (
                          <>
                            <Separator
                              orientation="vertical"
                              className="h-4 mx-1"
                            />
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setIsChatMinimized(false)}
                              className="h-6 px-2 text-xs"
                              title="Show Chat"
                            >
                              <ChevronLeft className="h-3 w-3 mr-1" />
                              Chat
                            </Button>
                          </>
                        )}
                      </div>
                    </div>

                    {/* Video Preview */}
                    <div
                      className="flex-1 bg-zinc-900 flex flex-col border border-border/50 rounded-lg overflow-hidden shadow-2xl relative"
                    >
                      <div className="flex-1 flex w-full">
                        {/* Always show video player - starts with empty composition */}
                        <DynamicVideoPlayer
                          blueprint={currentComposition}
                          compositionWidth={previewSettings.width}
                          compositionHeight={previewSettings.height}
                          backgroundColor={previewSettings.backgroundColor}
                          playerRef={playerRef}
                          selectedClipId={selectedClipId}
                          onSelectClip={setSelectedClipId}
                          onUpdateTransform={handleUpdateClipTransform}
                        />
                      </div>
                    </div>
                  </div>
                </ResizablePanel>
              </ResizablePanelGroup>
            </ResizablePanel>

            <ResizableHandle withHandle />

            {/* Timeline Panel - Resizable */}
            <ResizablePanel defaultSize={35} minSize={20} maxSize={60}>
              <div className="h-full border-t border-border bg-background p-4">
                {/* Always show timeline - starts with empty composition */}
                <TimelineView
                  blueprint={currentComposition}
                  className="h-full"
                  playerRef={playerRef}
                  currentFrame={timelineFrame} // Use timeline frame for scrubber position
                  fps={30}
                  onFrameUpdate={handleTimelineFrameUpdate} // Use custom handler
                  onDropMedia={handleDropMediaOnTimeline}
                  onMoveClip={handleMoveClip}
                  onSplitClip={handleSplitClip}
                  onDeleteClip={handleDeleteClip}
                  selectedClipId={selectedClipId}
                  onSelectClip={setSelectedClipId}
                  undoRedoActions={undoRedoActions}
                />
              </div>
            </ResizablePanel>
          </ResizablePanelGroup>
        </ResizablePanel>

        {/* Conditionally render chat panel - extends full height */}
        {!isChatMinimized && (
          <>
            <ResizableHandle withHandle />

            {/* Right Panel - Chat (full height) */}
            <ResizablePanel defaultSize={20} minSize={15} maxSize={35}>
              <div className="h-full border-l border-border">
                <ChatBox
                  mediaBinItems={mediaBinItems}
                  handleDropOnTrack={() => {}} // No-op since we don't have timeline integration yet
                  isMinimized={false}
                  onToggleMinimize={() => setIsChatMinimized(true)}
                  messages={chatMessages}
                  onMessagesChange={setChatMessages}
                  timelineState={{ tracks: [] }} // Empty timeline for now
                  isStandalonePreview={true}
                  currentComposition={JSON.stringify(currentComposition)} // Pass current blueprint as JSON string
                  onGenerateComposition={handleGenerateComposition} // AI generation function implemented!
                  isGeneratingComposition={isAiGenerating}
                  onAddGeneratedImage={handleAddGeneratedImage}
                  onUpdateMediaItem={handleUpdateMediaItem}
                  getToken={getToken}
                  initialEditProvider={selectedEditProvider}
                  initialAgentProvider={selectedAgentProvider}
                />
              </div>
            </ResizablePanel>
          </>
        )}
      </ResizablePanelGroup>

      {/* Provider Pairing Modal */}
      <ProviderPairingModal 
        isOpen={showProviderModal}
        onSelect={handleProviderPairingSelect}
      />

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="video/*,image/*,audio/*"
        multiple
        className="hidden"
        onChange={handleFileInputChange}
      />

      {/* Render Status as Toast */}
      {renderStatus && (
        <div className="fixed bottom-4 right-4 z-50">
          <RenderStatus renderStatus={renderStatus} />
        </div>
      )}
    </div>
  );
}
