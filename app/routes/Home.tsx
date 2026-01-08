import React, { useRef, useEffect, useCallback, useState } from "react";
import type { PlayerRef } from "@remotion/player";
import { ChevronLeft, LogOut, User } from "lucide-react";

// Components
import LeftPanel from "~/components/editor/LeftPanel";
import { DynamicVideoPlayer } from "~/composition/DynamicComposition";
import { calculateBlueprintDuration } from "~/composition/executeClipElement";
import { Button } from "~/components/ui/button";
import { Separator } from "~/components/ui/separator";
import { Input } from "~/components/ui/input";
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "~/components/ui/resizable";
import TimelineView from "~/components/editor/timeline/TimelineView";
import { ChatBox } from "~/components/editor/chat/ChatBox";
import { SessionHistory } from "~/components/editor/chat/SessionHistory";
import { ProviderPairingModal } from "~/components/editor/chat/ProviderPairingModal";
import { SettingsModal } from "~/components/editor/chat/SettingsModal";

// Hooks
import { useAuth } from "~/hooks/useAuth";
import { useMediaBin } from "~/hooks/useMediaBin";
import { useCompositionEditor } from "~/hooks/useCompositionEditor";
import { usePlayerControls } from "~/hooks/usePlayerControls";
import { useChatSession } from "~/hooks/useChatSession";
import { useAIGeneration } from "~/hooks/useAIGeneration";
import { useUndoRedoShortcuts } from "~/hooks/useUndoRedo";

// Types
import type { MediaBinItem } from "~/components/editor/timeline/types";
import type { AgentProvider, EditProvider } from "~/types/provider";

const PREVIEW_SETTINGS = {
  width: 1920,
  height: 1080,
  backgroundColor: "#000000",
  fps: 30,
};

export default function TimelineEditor() {
  const playerRef = useRef<PlayerRef>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Auth
  const { signOut, user, getToken } = useAuth();

  // UI State
  const [width, setWidth] = useState(1920);
  const [height, setHeight] = useState(1080);
  const [isChatMinimized, setIsChatMinimized] = useState(false);
  const [showProviderModal, setShowProviderModal] = useState(true);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [selectedEditProvider, setSelectedEditProvider] = useState<EditProvider>("gemini");
  const [selectedAgentProvider, setSelectedAgentProvider] = useState<AgentProvider>("gemini");
  const [selectedClipId, setSelectedClipId] = useState<string | null>(null);
  const [selectedItem, setSelectedItem] = useState<string | null>(null);
  const [durationInFrames, setDurationInFrames] = useState(90);
  const [mounted, setMounted] = useState(false);

  // Composition Editor
  const [composition, compositionActions] = useCompositionEditor();

  // Media Bin
  const {
    mediaBinItems,
    handleAddMediaToBin,
    handleAddTextToBin,
    handleAddDirectMediaBinItem,
    handleUpdateMediaItem,
    handleSetMediaBin,
    contextMenu,
    handleContextMenu,
    handleDeleteFromContext,
    handleSplitAudioFromContext,
    handleCloseContextMenu
  } = useMediaBin(() => {}, getToken);

  // Player Controls
  const [playerState, playerActions] = usePlayerControls(playerRef, composition);

  // Chat Session
  const [chatState, chatActions] = useChatSession(
    getToken,
    composition,
    mediaBinItems,
    compositionActions.set,
    handleSetMediaBin
  );

  // AI Generation
  const [aiState, aiActions] = useAIGeneration(
    composition,
    compositionActions.set,
    setDurationInFrames,
    handleAddDirectMediaBinItem,
    getToken,
    PREVIEW_SETTINGS
  );

  // Provider selection handler
  const handleProviderPairingSelect = (editProvider: EditProvider, agentProvider: AgentProvider) => {
    setSelectedEditProvider(editProvider);
    setSelectedAgentProvider(agentProvider);
    setShowProviderModal(false);
  };

  // Keyboard shortcuts
  const handleUndoRedoKeyDown = useUndoRedoShortcuts(compositionActions);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.shiftKey && e.key === "C") {
        e.preventDefault();
        navigator.clipboard.writeText(JSON.stringify(composition, null, 2));
        return;
      }
      handleUndoRedoKeyDown(e);
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [handleUndoRedoKeyDown, composition]);

  // Update duration when composition changes
  useEffect(() => {
    if (composition && composition.length > 0) {
      const calculatedDuration = calculateBlueprintDuration(composition);
      setDurationInFrames(Math.max(calculatedDuration, 1));
    } else {
      setDurationInFrames(90);
    }
  }, [composition]);

  // File input handler
  const handleAddMediaClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleFileInputChange = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        for (const file of Array.from(files)) {
          try {
            await handleAddMediaToBin(file);
          } catch (error) {
            console.error(`Failed to add ${file.name}:`, error);
          }
        }
        e.target.value = "";
      }
    },
    [handleAddMediaToBin]
  );

  // Mount guard
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
    <div
      className="h-screen flex flex-col bg-background text-foreground"
      onPointerDown={(e) => {
        if (e.button === 0) setSelectedItem(null);
      }}
    >
      {/* Header */}
      <header className="h-12 border-b border-border bg-background flex items-center justify-between px-4 shrink-0">
        <div className="flex items-center gap-3 ml-10">
          <h1 className="text-lg font-semibold tracking-tight">Screenwrite</h1>
        </div>
        <div className="flex items-center gap-2">
          {user && (
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0" title={user.email}>
              <User className="h-4 w-4" />
            </Button>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() => signOut()}
            className="h-8 px-3 text-xs font-medium"
          >
            <LogOut className="h-3.5 w-3.5 mr-1.5" />
            Sign Out
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        <SessionHistory
          sessions={chatState.sessions}
          currentSessionId={chatState.currentSessionId}
          loadingSessionId={chatState.loadingSessionId}
          isLoading={chatState.isSessionLoading}
          onNewSession={chatActions.startNewSession}
          onLoadSession={chatActions.loadSession}
          onDeleteSession={chatActions.deleteSession}
          onOpenSettings={() => setShowSettingsModal(true)}
        />

        <ResizablePanelGroup direction="horizontal" className="flex-1">
          <ResizablePanel defaultSize={isChatMinimized ? 100 : 80}>
            <ResizablePanelGroup direction="vertical">
              {/* Preview Section */}
              <ResizablePanel defaultSize={65} minSize={40}>
                <ResizablePanelGroup direction="horizontal">
                  {/* Left Panel */}
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
                        currentComposition={composition}
                        onUpdateClipElements={compositionActions.updateClipElements}
                      />
                    </div>
                  </ResizablePanel>

                  <ResizableHandle withHandle />

                  {/* Video Preview */}
                  <ResizablePanel defaultSize={75}>
                    <div className="h-full flex flex-col bg-background">
                      <div className="h-8 border-b border-border/50 bg-muted/30 flex items-center justify-between px-3 shrink-0">
                        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                          <span>Resolution:</span>
                          <div className="flex items-center gap-1">
                            <Input
                              type="number"
                              value={width}
                              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setWidth(Number(e.target.value))}
                              className="h-5 w-14 text-xs px-1 border-0 bg-muted/50"
                            />
                            <span>x</span>
                            <Input
                              type="number"
                              value={height}
                              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setHeight(Number(e.target.value))}
                              className="h-5 w-14 text-xs px-1 border-0 bg-muted/50"
                            />
                          </div>
                        </div>
                        {isChatMinimized && (
                          <div className="flex items-center gap-1">
                            <Separator orientation="vertical" className="h-4 mx-1" />
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
                          </div>
                        )}
                      </div>

                      <div className="flex-1 bg-zinc-900 flex flex-col border border-border/50 rounded-lg overflow-hidden shadow-2xl relative">
                        <div className="flex-1 flex w-full">
                          <DynamicVideoPlayer
                            blueprint={composition}
                            compositionWidth={PREVIEW_SETTINGS.width}
                            compositionHeight={PREVIEW_SETTINGS.height}
                            backgroundColor={PREVIEW_SETTINGS.backgroundColor}
                            playerRef={playerRef}
                            selectedClipId={selectedClipId}
                            onSelectClip={setSelectedClipId}
                            onUpdateTransform={compositionActions.updateClipTransform}
                            mediaLibrary={mediaBinItems
                              .filter((item: MediaBinItem) => item.name !== undefined)
                              .map((item: MediaBinItem) => ({
                                name: item.name,
                                mediaUrlLocal: item.mediaUrlLocal,
                                mediaUrlRemote: item.mediaUrlRemote,
                              }))}
                          />
                        </div>
                      </div>
                    </div>
                  </ResizablePanel>
                </ResizablePanelGroup>
              </ResizablePanel>

              <ResizableHandle withHandle />

              {/* Timeline */}
              <ResizablePanel defaultSize={35} minSize={20} maxSize={60}>
                <div className="h-full border-t border-border bg-background p-4">
                  <TimelineView
                    blueprint={composition}
                    className="h-full"
                    playerRef={playerRef}
                    currentFrame={playerState.timelineFrame}
                    fps={30}
                    onFrameUpdate={playerActions.setTimelineFrame}
                    onDropMedia={compositionActions.dropMedia}
                    onMoveClip={compositionActions.moveClip}
                    onSplitClip={compositionActions.splitClip}
                    onDeleteClip={compositionActions.deleteClip}
                    selectedClipId={selectedClipId}
                    onSelectClip={setSelectedClipId}
                    undoRedoActions={compositionActions}
                  />
                </div>
              </ResizablePanel>
            </ResizablePanelGroup>
          </ResizablePanel>

          {/* Chat Panel */}
          {!isChatMinimized && (
            <>
              <ResizableHandle withHandle />
              <ResizablePanel defaultSize={20} minSize={15} maxSize={35}>
                <div className="h-full border-l border-border">
                  <ChatBox
                    mediaBinItems={mediaBinItems}
                    handleDropOnTrack={() => {}}
                    isMinimized={false}
                    onToggleMinimize={() => setIsChatMinimized(true)}
                    messages={chatState.messages}
                    onMessagesChange={chatActions.setMessages}
                    timelineState={{ tracks: [] }}
                    isStandalonePreview={true}
                    currentComposition={JSON.stringify(composition)}
                    onGenerateComposition={aiActions.generateComposition}
                    isGeneratingComposition={aiState.isGenerating}
                    onAddGeneratedImage={aiActions.addGeneratedImage}
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
      </div>

      {/* Modals */}
      <ProviderPairingModal isOpen={showProviderModal} onSelect={handleProviderPairingSelect} />
      <SettingsModal
        isOpen={showSettingsModal}
        onClose={() => setShowSettingsModal(false)}
        selectedModel={selectedAgentProvider}
        onModelChange={setSelectedAgentProvider}
        selectedEditProvider={selectedEditProvider}
        onEditProviderChange={setSelectedEditProvider}
      />

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="video/*,image/*,audio/*"
        multiple
        className="hidden"
        onChange={handleFileInputChange}
      />
    </div>
  );
}
