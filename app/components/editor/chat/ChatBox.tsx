import { useState, useEffect, useRef, useCallback } from "react";
import axios from "axios";
import {
  Bot,
  Send,
  User,
  AtSign,
  FileVideo,
  FileImage,
  Type,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  X,
  Video,
  Clock,
  Music,
} from "lucide-react";
import { Button } from "~/components/ui/button";
import { Badge } from "~/components/ui/badge";
import { apiUrl } from "~/lib/api";
import { generateUUID } from "~/lib/uuid";

// Types
import type { MediaBinItem } from "~/components/editor/timeline/types";
import type { Message, ChatBoxProps } from "~/types/chat";

// Hooks
import { useChatInput } from "~/hooks/useChatInput";
import { useChatMediaOperations } from "~/hooks/useChatMediaOperations";
import { useChatWorkflow } from "~/hooks/useChatWorkflow";
import { useChatMessages } from "~/hooks/useChatMessages";

export function ChatBox({
  messages,
  onMessagesChange,
  mediaBinItems,
  mediaBinItemsRef,
  currentCompositionRef,
  timelineState,
  handleDropOnTrack,
  getToken,
  onGenerateComposition,
  onAddGeneratedImage,
  isStandalonePreview = false,
  initialAgentProvider = "gemini",
  initialEditProvider = "gemini",
  isGeneratingComposition = false,
  generationError,
  onRetryFix,
  onClearError,
  isMinimized = false,
  onToggleMinimize,
  className = "",
}: ChatBoxProps) {
  // Model selection state
  const [selectedModel, setSelectedModel] = useState(initialAgentProvider);
  const [selectedEditProvider, setSelectedEditProvider] = useState(initialEditProvider);
  const [showSendOptions, setShowSendOptions] = useState(false);
  const [sendWithMedia, setSendWithMedia] = useState(false);
  const [previewItem, setPreviewItem] = useState<MediaBinItem | null>(null);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const sendOptionsRef = useRef<HTMLDivElement>(null);

  // Sync model selections with props
  useEffect(() => {
    setSelectedModel(initialAgentProvider);
  }, [initialAgentProvider]);

  useEffect(() => {
    setSelectedEditProvider(initialEditProvider);
  }, [initialEditProvider]);

  // Helper to get authenticated headers
  const getAuthHeaders = useCallback(async () => {
    const token = await getToken();
    return {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    };
  }, [getToken]);

  // Chat messages utilities
  const {
    collapsedMessages,
    toggleMessageCollapsed,
    createDiff,
    formatText,
    formatTime,
  } = useChatMessages();

  // Media operations
  const {
    probeMedia,
    generateMedia,
    fetchStockVideos,
  } = useChatMediaOperations({
    getAuthHeaders,
    mediaBinItemsRef,
    mediaBinItems,
    onAddGeneratedImage,
    setCollapsedMessages: (fn) => {
      // Bridge to useChatMessages - we need to expose setter
      // For now, handle collapsed state locally for new messages
    },
  });

  // Workflow management
  const {
    isInSynthLoop,
    runAgentWorkflow,
    stopWorkflow,
  } = useChatWorkflow({
    getAuthHeaders,
    mediaBinItemsRef,
    currentCompositionRef,
    selectedModel,
    selectedEditProvider,
    onMessagesChange,
    onGenerateComposition,
    probeMedia,
    generateMedia,
    fetchStockVideos,
  });

  // Send message handler
  const handleSendMessageInternal = useCallback(async (
    content: string,
    itemsToSend: MediaBinItem[],
    includeAllMedia: boolean
  ) => {
    let messageContent = content;

    if (includeAllMedia && mediaBinItems.length > 0) {
      const mediaList = mediaBinItems.map((item) => `@${item.name}`).join(" ");
      messageContent = `${messageContent} ${mediaList}`;
      itemsToSend = [...itemsToSend, ...mediaBinItems.filter(item => 
        !itemsToSend.find(mentioned => mentioned.id === item.id)
      )];
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      content: messageContent,
      isUser: true,
      timestamp: new Date(),
    };

    const updatedMessages = [...messages, userMessage];
    onMessagesChange(prevMessages => [...prevMessages, userMessage]);

    try {
      if (isStandalonePreview) {
        await runAgentWorkflow(updatedMessages);
        return;
      }

      // Original timeline-based AI functionality
      const mentionedScrubberIds = itemsToSend.map(item => item.id);
      const token = await getToken();
      
      const response = await axios.post(apiUrl("/api/v1/agent/chat"), {
        message: messageContent,
        mentioned_scrubber_ids: mentionedScrubberIds,
        timeline_state: timelineState,
        mediabin_items: mediaBinItems,
      }, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });

      const functionCallResponse = response.data;
      let aiResponseContent = "";

      if (functionCallResponse.function_call) {
        const { function_call } = functionCallResponse;
        
        try {
          if (function_call.function_name === "LLMAddScrubberToTimeline") {
            const mediaItem = mediaBinItems.find(
              item => item.id === function_call.scrubber_id
            );

            if (!mediaItem) {
              aiResponseContent = `Error: Media item with ID "${function_call.scrubber_id}" not found in the media bin.`;
            } else {
              handleDropOnTrack(mediaItem, function_call.track_id, function_call.drop_left_px);
              aiResponseContent = `Successfully added "${mediaItem.name}" to ${function_call.track_id} at position ${function_call.drop_left_px}px.`;
            }
          } else {
            aiResponseContent = `Unknown function: ${function_call.function_name}`;
          }
        } catch (error) {
          aiResponseContent = `Error executing function: ${
            error instanceof Error ? error.message : "Unknown error"
          }`;
        }
      } else {
        aiResponseContent = "I understand your request, but I couldn't determine a specific action to take. Could you please be more specific?";
      }

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: aiResponseContent,
        isUser: false,
        timestamp: new Date(),
      };

      onMessagesChange(prevMessages => [...prevMessages, aiMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `Sorry, I encountered an error while processing your request. Please try again.`,
        isUser: false,
        sender: 'system',
        timestamp: new Date(),
      };
      
      onMessagesChange(prevMessages => [...prevMessages, errorMessage]);
    }
  }, [
    messages,
    mediaBinItems,
    onMessagesChange,
    isStandalonePreview,
    runAgentWorkflow,
    getToken,
    timelineState,
    handleDropOnTrack
  ]);

  // Input handling
  const {
    inputValue,
    showMentions,
    mentionQuery,
    selectedMentionIndex,
    mentionedItems,
    textareaHeight,
    filteredMentions,
    inputRef,
    mentionsRef,
    handleInputChange,
    handleKeyPress,
    insertMention,
    clearInput,
    setMentionedItems,
  } = useChatInput({
    mediaBinItems,
    onSendMessage: (content, items, includeAll) => {
      handleSendMessageInternal(content, items, includeAll);
      clearInput();
    },
  });

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  // Click outside handler for send options
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        sendOptionsRef.current &&
        !sendOptionsRef.current.contains(event.target as Node)
      ) {
        setShowSendOptions(false);
      }
    };

    if (showSendOptions) {
      document.addEventListener("mousedown", handleClickOutside);
      return () =>
        document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [showSendOptions]);

  // Handle retry button click
  const handleRetry = useCallback((message: Message) => {
    if (message.retryData?.originalMessage) {
      runAgentWorkflow(messages);
    }
  }, [messages, runAgentWorkflow]);

  // Helper to generate unique name for media items
  const generateUniqueName = (baseName: string, existingItems: MediaBinItem[]): string => {
    let name = baseName;
    let counter = 1;
    while (existingItems.some(item => item.name === name)) {
      name = `${baseName} (${counter})`;
      counter++;
    }
    return name;
  };

  return (
    <div className={`h-full flex flex-col bg-background ${className}`}>
      {/* Chat Header */}
      <div className="h-9 border-b border-border/50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 flex items-center justify-between px-3 shrink-0">
        <div className="flex items-center gap-2">
          <Bot className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="text-sm font-medium tracking-tight">Ask Screenwrite</span>
        </div>

        {onToggleMinimize && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggleMinimize}
            className="h-6 w-6 p-0 text-muted-foreground hover:text-foreground"
            title={isMinimized ? "Expand chat" : "Minimize chat"}
          >
            {isMinimized ? (
              <ChevronLeft className="h-3 w-3" />
            ) : (
              <ChevronRight className="h-3 w-3" />
            )}
          </Button>
        )}
      </div>

      {/* Content Area */}
      <div className="flex-1 flex flex-col">
        {messages.length === 0 ? (
          // Default clean state
          <div className="flex-1 flex flex-col items-center justify-center p-6 text-center">
            <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
              <Bot className="h-6 w-6 text-primary" />
            </div>
            <h2 className="text-lg font-semibold mb-2">Ask Screenwrite</h2>
            <p className="text-sm text-muted-foreground mb-8 max-w-xs leading-relaxed">
              Screenwrite is your AI assistant for video editing. Ask questions, get
              help with timeline operations, or request specific edits.
            </p>
            <div className="space-y-2 text-xs text-muted-foreground">
              <div className="flex items-center gap-2">
                <AtSign className="h-3 w-3" />
                <span>to chat with media</span>
              </div>
              <div className="flex items-center gap-2">
                <kbd className="px-1.5 py-0.5 text-xs bg-muted rounded">Enter</kbd>
                <span>to send</span>
              </div>
              <div className="flex items-center gap-2">
                <kbd className="px-1.5 py-0.5 text-xs bg-muted rounded">Shift</kbd>
                <span>+</span>
                <kbd className="px-1.5 py-0.5 text-xs bg-muted rounded">Enter</kbd>
                <span>for new line</span>
              </div>
            </div>
          </div>
        ) : (
          // Messages Area
          <div
            ref={scrollContainerRef}
            className="flex-1 overflow-y-auto p-3 scroll-smooth"
            style={{ maxHeight: "calc(100vh - 200px)" }}
          >
            <div className="space-y-3">
              {/* Error Display */}
              {generationError?.hasError && (
                <div className="flex justify-start">
                  <div className="max-w-[90%] rounded-lg px-3 py-3 text-xs bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-700 mr-8">
                    <div className="flex items-start gap-2">
                      <AlertCircle className="h-4 w-4 mt-0.5 shrink-0 text-red-600 dark:text-red-400" />
                      <div className="flex-1">
                        <div className="font-medium text-red-800 dark:text-red-200 mb-1">
                          Generation Error
                        </div>
                        <div className="text-red-700 dark:text-red-300 mb-2">
                          {generationError.errorMessage}
                        </div>
                        
                        {generationError.canRetry && onRetryFix && (
                          <div className="flex gap-2 mt-2">
                            <button
                              onClick={async () => {
                                await onRetryFix();
                              }}
                              className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded-md transition-colors"
                              disabled={isGeneratingComposition}
                            >
                              {isGeneratingComposition ? "Fixing..." : "Try Again"}
                            </button>
                            {onClearError && (
                              <button
                                onClick={onClearError}
                                className="px-3 py-1 bg-gray-600 hover:bg-gray-700 text-white text-xs rounded-md transition-colors"
                              >
                                Dismiss
                              </button>
                            )}
                          </div>
                        )}
                        
                        {!generationError.canRetry && onClearError && (
                          <button
                            onClick={onClearError}
                            className="px-3 py-1 bg-gray-600 hover:bg-gray-700 text-white text-xs rounded-md transition-colors mt-2"
                          >
                            Dismiss
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              {messages.map((message) => (
                message.alreadyInUI ? null :
                message.isSystemMessage ? (
                  <div key={message.id} className="px-3 py-1 text-xs text-muted-foreground">
                    <div>{message.content}</div>
                    
                    {/* Sentence timestamps collapsible UI */}
                    {message.word_timestamps && message.word_timestamps.length > 0 && (
                      <div className="mt-2 border border-border/50 rounded-md overflow-hidden max-w-md">
                        <button
                          onClick={() => toggleMessageCollapsed(message.id)}
                          className="w-full px-3 py-2 bg-muted/30 hover:bg-muted/50 transition-colors flex items-center justify-between text-xs"
                        >
                          <span className="font-medium">Sentence Timestamps ({message.word_timestamps.length} sentences)</span>
                          <ChevronDown className={`h-3 w-3 transition-transform ${
                            !collapsedMessages.has(message.id) ? '' : 'rotate-180'
                          }`} />
                        </button>
                        {collapsedMessages.has(message.id) && (
                          <div className="p-3 bg-muted/20 max-h-60 overflow-y-auto">
                            <div className="flex flex-wrap gap-2 text-xs font-mono">
                              {message.word_timestamps.map((ts, idx) => (
                                <div key={idx} className="flex items-center gap-2 px-2 py-1 bg-background/50 rounded border border-border/30">
                                  <span className="font-medium">{ts.word}</span>
                                  <span className="text-muted-foreground text-[10px]">
                                    {ts.start.toFixed(2)}s-{ts.end.toFixed(2)}s
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                    
                    {/* Composition diff collapsible UI */}
                    {message.compositionDiff && (
                      <div className="mt-2 border border-border/50 rounded-md overflow-hidden">
                        <button
                          onClick={() => toggleMessageCollapsed(`${message.id}-diff`)}
                          className="w-full px-3 py-2 bg-muted/30 hover:bg-muted/50 transition-colors flex items-center justify-between text-xs"
                        >
                          <span className="font-medium">Show composition changes</span>
                          <ChevronDown className={`h-3 w-3 transition-transform ${
                            !collapsedMessages.has(`${message.id}-diff`) ? '' : 'rotate-180'
                          }`} />
                        </button>
                        {collapsedMessages.has(`${message.id}-diff`) && (
                          <div className="p-3 bg-muted/20 max-h-96 overflow-auto">
                            <div className="font-mono text-[11px] leading-relaxed whitespace-pre-wrap">
                              {createDiff(message.compositionDiff.before, message.compositionDiff.after).map((line, idx) => (
                                <div key={idx} className={`${
                                  line.type === 'removed' ? 'bg-red-500/10 text-red-400 border-l-2 border-red-500 pl-2' :
                                  line.type === 'added' ? 'bg-green-500/10 text-green-400 border-l-2 border-green-500 pl-2' :
                                  'text-muted-foreground/60'
                                }`}>
                                  <span className="inline-block w-4 text-muted-foreground/40 mr-2 select-none">
                                    {line.type === 'removed' ? '-' : line.type === 'added' ? '+' : ' '}
                                  </span>
                                  {line.content || '\u00A0'}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                    
                    {message.hasRetryButton && (
                      <Button
                        size="sm"
                        variant="outline"
                        className="ml-2 text-xs h-6"
                        onClick={() => handleRetry(message)}
                      >
                        Retry
                      </Button>
                    )}
                  </div>
                ) : (
                  <div
                    key={message.id}
                    className={`flex ${
                      message.isUser ? "justify-end" : "justify-start"
                    }`}
                  >
                    <div
                      className={`max-w-[80%] rounded-lg px-3 py-2 text-xs ${
                        message.isUser
                          ? "bg-primary text-primary-foreground ml-8"
                          : message.isExplanationMode
                          ? "bg-green-100 dark:bg-green-900/30 border border-green-300 dark:border-green-700 mr-8"
                          : message.isAnalysisResult
                          ? "bg-slate-800 dark:bg-slate-900 text-white mr-8 cursor-pointer hover:bg-slate-700 dark:hover:bg-slate-800 transition-colors"
                          : "mr-8"
                      }`}
                      style={!message.isUser && !message.isExplanationMode && !message.isAnalysisResult ? {
                        backgroundColor: 'hsl(0, 0%, 9.9%)',
                        color: 'hsl(0, 0%, 85%)'
                      } : undefined}
                      onClick={message.isAnalysisResult ? () => toggleMessageCollapsed(message.id) : undefined}
                    >
                    <div className="flex items-start gap-2">
                      {!message.isUser && (
                        <Bot className={`h-3 w-3 mt-0.5 shrink-0 ${
                          message.isExplanationMode
                            ? "text-green-600 dark:text-green-400"
                            : message.isAnalysisResult
                            ? "text-slate-300"
                            : "text-muted-foreground"
                        }`} />
                      )}
                      <div className="flex-1 min-w-0">
                        {message.isExplanationMode && (
                          <div className="text-xs font-medium text-green-700 dark:text-green-300 mb-1">
                            Changes made:
                          </div>
                        )}
                        {message.isAnalysisResult ? (
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-medium text-slate-200">Analysis Result</span>
                              <ChevronDown className={`h-3 w-3 transition-transform ${
                                collapsedMessages.has(message.id) ? 'rotate-180' : ''
                              }`} />
                            </div>
                            {!collapsedMessages.has(message.id) && (
                              <p className="leading-relaxed break-words overflow-wrap-anywhere">
                                {formatText(message.content)}
                              </p>
                            )}
                          </div>
                        ) : (
                          <p className={`leading-relaxed break-words overflow-wrap-anywhere ${
                            message.isExplanationMode
                              ? "text-green-800 dark:text-green-200"
                              : ""
                          }`}>
                            {formatText(message.content)}
                          </p>
                        )}

                        {/* Video Selection UI */}
                        {message.isVideoSelection && message.videoOptions && (
                          <div className="mt-3 grid grid-cols-1 gap-2">
                            {message.videoOptions.map((video) => (
                              <div
                                key={video.id}
                                className="border border-gray-300 dark:border-gray-600 rounded-lg p-3 cursor-pointer hover:border-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
                                onClick={() => {
                                  const title = video.title;
                                  const name = generateUniqueName(title, mediaBinItemsRef.current);

                                  const mediaItem: MediaBinItem = {
                                    id: generateUUID(),
                                    name,
                                    title,
                                    mediaType: "video",
                                    mediaUrlLocal: null,
                                    mediaUrlRemote: video.downloadUrl,
                                    media_width: video.width || 0,
                                    media_height: video.height || 0,
                                    durationInSeconds: video.durationInSeconds || 0,
                                    text: null,
                                    isUploading: false,
                                    uploadProgress: null,
                                    upload_status: 'uploaded',
                                    gemini_file_id: null,
                                    left_transition_id: null,
                                    right_transition_id: null,
                                  };
                                  setPreviewItem(mediaItem);
                                }}
                              >
                                <div className="flex gap-3 items-center">
                                  <div className="flex-shrink-0">
                                    <img
                                      src={video.thumbnailUrl}
                                      alt={video.title}
                                      className="w-16 h-9 object-cover rounded border bg-gray-100 dark:bg-gray-800 block"
                                    />
                                  </div>
                                  <div className="flex-1 min-w-0 overflow-hidden">
                                    <div className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                                      {video.title}
                                    </div>
                                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                                      Duration: {video.duration}
                                    </div>
                                    <div className="text-xs text-gray-600 dark:text-gray-300 mt-0.5 line-clamp-2">
                                      {video.description}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                        <span className="text-xs opacity-70 mt-1 block">
                          {formatTime(message.timestamp)}
                        </span>
                      </div>
                      {message.isUser && (
                        <User className="h-3 w-3 mt-0.5 text-primary-foreground/70 shrink-0" />
                      )}
                    </div>
                  </div>
                </div>
                )
              ))}

              {/* Loading indicator while in synth loop */}
              {isInSynthLoop && (
                <div className="px-3 py-2 flex items-center gap-2">
                  <div className="flex items-start gap-2">
                    <Bot className="h-3 w-3 mt-0.5 shrink-0 text-muted-foreground" />
                    <div className="flex items-center gap-1 pt-1">
                      <div className="flex space-x-1">
                        <div className="w-1 h-1 bg-muted-foreground rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                        <div className="w-1 h-1 bg-muted-foreground rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                        <div className="w-1 h-1 bg-muted-foreground rounded-full animate-bounce"></div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Mentions popup */}
            {showMentions && (
              <div
                ref={mentionsRef}
                className="absolute bottom-full left-4 right-4 mb-2 bg-background border border-border/50 rounded-lg shadow-lg max-h-40 overflow-y-auto z-50"
              >
                {filteredMentions.map((item, index) => (
                  <div
                    key={item.id}
                    className={`px-3 py-2 text-xs cursor-pointer flex items-center gap-2 ${
                      index === selectedMentionIndex
                        ? "bg-accent text-accent-foreground"
                        : "hover:bg-muted"
                    }`}
                    onClick={() => insertMention(item)}
                  >
                    <div className="w-6 h-6 bg-muted/50 rounded flex items-center justify-center">
                      {item.mediaType === "video" ? (
                        <FileVideo className="h-3 w-3 text-muted-foreground" />
                      ) : item.mediaType === "image" ? (
                        <FileImage className="h-3 w-3 text-muted-foreground" />
                      ) : item.mediaType === "audio" ? (
                        <Music className="h-3 w-3 text-muted-foreground" />
                      ) : (
                        <Type className="h-3 w-3 text-muted-foreground" />
                      )}
                    </div>
                    <span className="flex-1 truncate">{item.name}</span>
                    <span className="text-xs text-muted-foreground">
                      {item.mediaType}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* Send Options Dropdown */}
            {showSendOptions && (
              <div
                ref={sendOptionsRef}
                className="absolute bottom-full right-4 mb-2 bg-background border border-border/50 rounded-md shadow-lg z-50 min-w-48"
              >
                <div className="p-1">
                  <div
                    className="px-3 py-2 text-xs cursor-pointer hover:bg-muted rounded flex items-center justify-between"
                    onClick={() => {
                      setSendWithMedia(false);
                      setShowSendOptions(false);
                      if (inputValue.trim()) {
                        handleSendMessageInternal(inputValue.trim(), mentionedItems, false);
                        clearInput();
                      }
                    }}
                  >
                    <span>Send</span>
                    <span className="text-xs text-muted-foreground font-mono">Enter</span>
                  </div>
                  <div
                    className="px-3 py-2 text-xs cursor-pointer hover:bg-muted rounded flex items-center justify-between"
                    onClick={() => {
                      setSendWithMedia(true);
                      setShowSendOptions(false);
                      if (inputValue.trim()) {
                        handleSendMessageInternal(inputValue.trim(), mentionedItems, true);
                        clearInput();
                      }
                    }}
                  >
                    <span>Send with all Media</span>
                  </div>
                  <div
                    className="px-3 py-2 text-xs cursor-pointer hover:bg-muted rounded flex items-center justify-between"
                    onClick={() => {
                      onMessagesChange(() => []);
                      setShowSendOptions(false);
                      if (inputValue.trim()) {
                        handleSendMessageInternal(inputValue.trim(), mentionedItems, false);
                        clearInput();
                      }
                    }}
                  >
                    <span>Send to New Chat</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Input Area */}
        <div className="border-t border-border/50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="p-3 relative">
            <div className="relative">
              <textarea
                ref={inputRef}
                value={inputValue}
                onChange={handleInputChange}
                onKeyDown={(e) => handleKeyPress(e, sendWithMedia)}
                placeholder="Ask Screenwrite to create or edit your video..."
                className="w-full resize-none border-0 bg-transparent text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-0 pr-12 overflow-hidden"
                style={{ height: `${textareaHeight}px` }}
              />
              
              <div className="absolute right-2 bottom-1 flex items-center gap-1">
                {(inputValue.trim() || mentionedItems.length > 0) && !isInSynthLoop && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0 text-muted-foreground hover:text-foreground relative"
                    onClick={(e: React.MouseEvent) => {
                      e.stopPropagation();
                      setShowSendOptions(!showSendOptions);
                    }}
                  >
                    <ChevronDown className="h-3 w-3" />
                  </Button>
                )}
                
                {isInSynthLoop ? (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0 text-destructive hover:text-destructive/80 hover:bg-destructive/10"
                    onClick={stopWorkflow}
                    title="Stop agent workflow"
                  >
                    <X className="h-3 w-3" />
                  </Button>
                ) : (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0 text-primary hover:text-primary/80 hover:bg-primary/10"
                    onClick={() => {
                      if (inputValue.trim()) {
                        handleSendMessageInternal(inputValue.trim(), mentionedItems, sendWithMedia);
                        clearInput();
                      }
                    }}
                    disabled={!inputValue.trim() && mentionedItems.length === 0}
                  >
                    <Send className="h-3 w-3" />
                  </Button>
                )}
              </div>
            </div>

            {mentionedItems.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2 pt-2 border-t border-border/50">
                {mentionedItems.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center gap-1 px-2 py-1 bg-muted rounded text-xs"
                  >
                    <div className="w-3 h-3 bg-muted-foreground/20 rounded flex items-center justify-center">
                      {item.mediaType === "video" ? (
                        <FileVideo className="h-2 w-2 text-muted-foreground" />
                      ) : item.mediaType === "image" ? (
                        <FileImage className="h-2 w-2 text-muted-foreground" />
                      ) : item.mediaType === "audio" ? (
                        <Music className="h-2 w-2 text-muted-foreground" />
                      ) : (
                        <Type className="h-2 w-2 text-muted-foreground" />
                      )}
                    </div>
                    <span className="truncate max-w-24">{item.name}</span>
                    <button
                      onClick={() => setMentionedItems(prev => prev.filter(i => i.id !== item.id))}
                      className="text-muted-foreground hover:text-foreground ml-1"
                    >
                      <X className="h-2 w-2" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Media Preview Modal */}
      {previewItem && (
        <div 
          className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[60]"
          onClick={() => setPreviewItem(null)}
        >
          <div 
            className="bg-card border border-border rounded-lg shadow-2xl max-w-4xl max-h-[90vh] w-full mx-4 overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-muted/30">
              <div className="flex items-center gap-3">
                <Video className="h-5 w-5 text-muted-foreground" />
                <div>
                  <h3 className="text-sm font-semibold text-foreground">
                    {previewItem.title || previewItem.name}
                  </h3>
                  <div className="flex items-center gap-2 mt-0.5">
                    <Badge variant="secondary" className="text-xs">
                      {previewItem.mediaType}
                    </Badge>
                    {previewItem.media_width && previewItem.media_height && (
                      <span className="text-xs text-muted-foreground">
                        {previewItem.media_width} x {previewItem.media_height}
                      </span>
                    )}
                    {previewItem.durationInSeconds > 0 && (
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {previewItem.durationInSeconds.toFixed(1)}s
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <button
                onClick={() => setPreviewItem(null)}
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="p-4 max-h-[calc(90vh-80px)] overflow-auto">
              {previewItem.mediaType === 'video' && (
                <video
                  src={previewItem.mediaUrlLocal || previewItem.mediaUrlRemote || ''}
                  controls
                  autoPlay
                  className="w-full rounded border border-border bg-black"
                  style={{ maxHeight: 'calc(90vh - 200px)' }}
                />
              )}
              {previewItem.mediaType === 'image' && (
                <img
                  src={previewItem.mediaUrlLocal || previewItem.mediaUrlRemote || ''}
                  alt={previewItem.name}
                  className="w-full rounded border border-border"
                  style={{ maxHeight: 'calc(90vh - 200px)', objectFit: 'contain' }}
                />
              )}
              {previewItem.mediaType === 'audio' && (
                <div className="flex flex-col items-center justify-center py-12">
                  <Music className="h-16 w-16 text-muted-foreground mb-4" />
                  <audio
                    src={previewItem.mediaUrlLocal || previewItem.mediaUrlRemote || ''}
                    controls
                    autoPlay
                    className="w-full max-w-md"
                  />
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
