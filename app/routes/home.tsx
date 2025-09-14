import React, { useRef, useEffect, useCallback, useState } from "react";
import type { PlayerRef } from "@remotion/player";
import * as Remotion from "remotion";
import { TransitionSeries, linearTiming, springTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { slide } from "@remotion/transitions/slide";
import { wipe } from "@remotion/transitions/wipe";
import { flip } from "@remotion/transitions/flip";
import { iris } from "@remotion/transitions/iris";
import { none } from "@remotion/transitions/none";
import { interp } from "../utils/animations";
import axios from "axios";
import { apiUrl } from "~/utils/api";
import {
  Moon,
  Sun,
  Upload,
  ChevronLeft,
} from "lucide-react";

import { useTheme } from "next-themes";

// Components
import LeftPanel from "~/components/editor/LeftPanel";
import { DynamicVideoPlayer } from "~/video-compositions/DynamicComposition";
import { calculateBlueprintDuration } from "~/video-compositions/executeClipElement";
import { sampleBlueprint, complexTestBlueprint } from "~/video-compositions/TestBlueprint";
import { edgeCaseTestBlueprint } from "~/video-compositions/EdgeCaseTestBlueprint";
import { allTransitionsTestBlueprint } from "~/video-compositions/AllTransitionsTestBlueprint";
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


// Types and constants
import { type Transition, type MediaBinItem } from "~/components/timeline/types";
import { useNavigate } from "react-router";

// Custom Timeline
import TimelineView from "../components/custom-timeline/TimelineView"; // direct relative path to bust alias cache
import { ChatBox } from "~/components/chat/ChatBox";

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

  const { theme, setTheme } = useTheme();

  const navigate = useNavigate();

  const [width, setWidth] = useState<number>(1920);
  const [height, setHeight] = useState<number>(1080);
  const [isAutoSize, setIsAutoSize] = useState<boolean>(false);
  const [isChatMinimized, setIsChatMinimized] = useState<boolean>(true);

    // Video playback state
  const [durationInFrames, setDurationInFrames] = useState<number>(1); // Minimal duration - gets updated by blueprint

  // Blueprint state - now the only mode
  const [testBlueprint, setTestBlueprint] = useState<CompositionBlueprint>(() => edgeCaseTestBlueprint);
  const [currentTestType, setCurrentTestType] = useState<'orphaned' | 'all-transitions'>('orphaned');

  // Function to switch between different test blueprints
  const switchTestBlueprint = (testType: 'orphaned' | 'all-transitions') => {
    setCurrentTestType(testType);
    if (testType === 'orphaned') {
      setTestBlueprint(edgeCaseTestBlueprint);
      setDurationInFrames(32 * 30); // 32 seconds for orphaned transitions test
    } else {
      setTestBlueprint(allTransitionsTestBlueprint);
      setDurationInFrames(18 * 30); // 18 seconds for all transitions test
    }
  };

  const [chatMessages, setChatMessages] = useState<Message[]>([]);
  const [mounted, setMounted] = useState(false)

  // AI generation state
  const [isGeneratingComposition, setIsGeneratingComposition] = useState<boolean>(false);
  const [aiGeneratedBlueprint, setAiGeneratedBlueprint] = useState<CompositionBlueprint | null>(null);

  // video player media selection state
  const [selectedItem, setSelectedItem] = useState<string | null>(null);
  
  // Video playback state for scrubber
  const [currentFrame, setCurrentFrame] = useState<number>(0);



  const {
    mediaBinItems,
    handleAddMediaToBin,
    handleAddTextToBin,
    contextMenu,
    handleContextMenu,
    handleDeleteFromContext,
    handleSplitAudioFromContext,
    handleCloseContextMenu
  } = useMediaBin(() => {}); // Empty function since we don't need timeline integration

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

  // Update duration when blueprint changes
  useEffect(() => {
    // Calculate duration from current test blueprint
    const calculatedDuration = calculateBlueprintDuration(testBlueprint);
    setDurationInFrames(calculatedDuration);
  }, [testBlueprint]);

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
      };

      const handleSeeked = (event: { detail: { frame: number } }) => {
        setCurrentFrame(event.detail.frame);
      };

      // Listen to the player's frame updates for real-time position
      player.addEventListener('frameupdate', handleFrameUpdate);
      player.addEventListener('seeked', handleSeeked);

      // Continuous polling for smooth scrubber movement during playback
      const interval = setInterval(() => {
        const currentPlayerFrame = player.getCurrentFrame();
        setCurrentFrame(currentPlayerFrame);
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
  const handleGenerateComposition = useCallback(async (userRequest: string, mediaBinItems: MediaBinItem[]): Promise<boolean> => {
    console.log("🤖 AI Generation: Starting composition generation for:", userRequest);
    setIsGeneratingComposition(true);
    
    try {
      // Call the Python backend API
      const response = await axios.post(apiUrl("/ai/generate-composition", true), {
        user_request: userRequest,
        preview_settings: previewSettings,
        media_library: mediaBinItems.map(item => ({
          id: item.id,
          name: item.name,
          type: item.mediaType,
          src: item.mediaUrlLocal || item.mediaUrlRemote,
        })),
        current_generated_code: null,
        conversation_history: [],
        preview_frame: null,
      });

      console.log("🤖 AI Generation: Received response:", response.data);

      if (response.data.success && response.data.composition_code) {
        try {
          // Parse the JSON response as CompositionBlueprint
          const blueprintJson = JSON.parse(response.data.composition_code);
          console.log("🤖 AI Generation: Parsed blueprint:", blueprintJson);

          // Set the AI generated blueprint as active
          setAiGeneratedBlueprint(blueprintJson);
          setTestBlueprint(blueprintJson);
          
          // Calculate and set duration
          const calculatedDuration = calculateBlueprintDuration(blueprintJson);
          setDurationInFrames(calculatedDuration);

          console.log("🤖 AI Generation: Blueprint applied successfully, duration:", calculatedDuration);
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
      setIsGeneratingComposition(false);
    }
  }, [previewSettings]);

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
          {/* Theme Toggle */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className="h-7 w-7 p-0 hover:bg-muted"
          >
            {theme === "dark" ? (
              <Sun className="h-3.5 w-3.5" />
            ) : (
              <Moon className="h-3.5 w-3.5" />
            )}
          </Button>

          <Separator orientation="vertical" className="h-4 mx-1" />

          {/* Import/Export */}
          <Button
            variant="ghost"
            size="sm"
            onClick={handleAddMediaClick}
            className="h-7 px-2 text-xs"
          >
            <Upload className="h-3 w-3 mr-1" />
            Import
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
                      contextMenu={contextMenu}
                      handleContextMenu={handleContextMenu}
                      handleDeleteFromContext={handleDeleteFromContext}
                      handleSplitAudioFromContext={handleSplitAudioFromContext}
                      handleCloseContextMenu={handleCloseContextMenu}
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
                            disabled={isAutoSize}
                            className="h-5 w-14 text-xs px-1 border-0 bg-muted/50"
                          />
                          <span>×</span>
                          <Input
                            type="number"
                            value={height}
                            onChange={(e) =>
                              setHeight(Number(e.target.value))
                            }
                            disabled={isAutoSize}
                            className="h-5 w-14 text-xs px-1 border-0 bg-muted/50"
                          />
                        </div>
                      </div>

                      <div className="flex items-center gap-1">
                        <div className="flex items-center gap-1">
                          <Switch
                            id="auto-size"
                            checked={isAutoSize}
                            onCheckedChange={handleAutoSizeChange}
                            className="scale-75"
                          />
                          <Label htmlFor="auto-size" className="text-xs">
                            Auto
                          </Label>
                        </div>

                        {/* TODO: Add blueprint-specific controls */}

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
                      className={`flex-1 ${theme === "dark" ? "bg-zinc-900" : "bg-zinc-200/70"
                        } flex flex-col items-center justify-center p-3 border border-border/50 rounded-lg overflow-hidden shadow-2xl relative`}
                    >
                      {/* Sample Content Button */}
                      <div className="absolute top-2 right-2 flex items-center gap-2 z-10">
                        <Badge 
                          variant={aiGeneratedBlueprint ? "default" : "outline"} 
                          className={`text-xs ${aiGeneratedBlueprint ? "bg-green-600 text-white" : ""}`}
                        >
                          {aiGeneratedBlueprint ? "AI Generated" : "Blueprint Mode"}
                        </Badge>
                        {!aiGeneratedBlueprint && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              const newTestType = currentTestType === 'orphaned' ? 'all-transitions' : 'orphaned';
                              switchTestBlueprint(newTestType);
                            }}
                            className="text-xs h-6"
                          >
                            {currentTestType === 'orphaned' ? 'Orphaned Tests' : 'All Transitions'}
                          </Button>
                        )}
                        {aiGeneratedBlueprint && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setAiGeneratedBlueprint(null);
                              switchTestBlueprint('orphaned');
                            }}
                            className="text-xs h-6"
                          >
                            Back to Test Mode
                          </Button>
                        )}
                      </div>

                      <div className="flex-1 flex items-center justify-center w-full">
                        {/* Blueprint-only video player */}
                        <DynamicVideoPlayer
                          blueprint={testBlueprint}
                          compositionWidth={previewSettings.width}
                          compositionHeight={previewSettings.height}
                          backgroundColor={previewSettings.backgroundColor}
                          playerRef={playerRef}
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
                <TimelineView
                  blueprint={testBlueprint}
                  className="h-full"
                  playerRef={playerRef}
                  currentFrame={currentFrame}
                  fps={30}
                  onFrameUpdate={setCurrentFrame}
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
                  onGenerateComposition={handleGenerateComposition} // AI generation function implemented!
                  isGeneratingComposition={isGeneratingComposition}
                  currentComposition={undefined}
                  generationError={undefined}
                  onRetryFix={undefined}
                  onClearError={undefined}
                />
              </div>
            </ResizablePanel>
          </>
        )}
      </ResizablePanelGroup>

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
