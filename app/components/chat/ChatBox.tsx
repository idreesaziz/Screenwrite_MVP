import React, { useState, useRef, useEffect, useCallback } from "react";
import {
  Send,
  Bot,
  User,
  ChevronDown,
  AtSign,
  FileVideo,
  FileImage,
  Type,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  X,
  Play,
  Video,
  Clock,
  Music,
} from "lucide-react";
import { Button } from "~/components/ui/button";
import { Badge } from "~/components/ui/badge";
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "~/components/ui/dropdown-menu";
import { type MediaBinItem, type TimelineState } from "../timeline/types";
import { cn } from "~/lib/utils";
import axios from "axios";
import { apiUrl, getApiBaseUrl } from "~/utils/api";
import { generateUUID } from "~/utils/uuid";
import type { GetTokenFn } from "~/utils/authApi";
import { 
  logUserMessage, 
  logSynthCall, 
  logSynthResponse, 
  logProbeStart, 
  logProbeAnalysis, 
  logProbeError,
  logEditExecution,
  logEditResult,
  logChatResponse,
  logWorkflowComplete 
} from "~/utils/fileLogger";

// llm tools
import { llmAddScrubberToTimeline } from "~/utils/llm-handler";

// Conversational Synth
import { ConversationalSynth, type SynthContext, type ConversationMessage, type SynthResponse, type ConversationSender } from "./ConversationalSynth";

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
  sender?: ConversationSender;
  isExplanationMode?: boolean; // For post-edit explanations
  isAnalysisResult?: boolean; // For analysis results that appear in darker bubbles
  isSystemMessage?: boolean; // For system messages (analyzing, generating, etc.) that appear as raw text
  hasRetryButton?: boolean; // For messages that allow retry
  retryData?: {
    originalMessage: string;
  }; // Data needed for retry
  isVideoSelection?: boolean; // For video selection messages
  videoOptions?: {
    id: number;
    title: string;
    duration: string;
    description: string;
    thumbnailUrl: string;
    downloadUrl: string;
    pexelsUrl: string;
    width: number;
    height: number;
    durationInSeconds: number;
  }[]; // Video options for selection
  isWaitingForAnalysis?: boolean; // For messages waiting on analysis result
  fileName?: string; // Associated file name for analysis
  alreadyInUI?: boolean; // Internal flag: message already added to UI, skip duplicate addition
}

interface ChatBoxProps {
  className?: string;
  mediaBinItems: MediaBinItem[];
  handleDropOnTrack: (
    item: MediaBinItem,
    trackId: string,
    dropLeftPx: number
  ) => void;
  isMinimized?: boolean;
  onToggleMinimize?: () => void;
  messages: Message[];
  onMessagesChange: (updater: (messages: Message[]) => Message[]) => void;
  timelineState: TimelineState;
  // New props for AI composition generation
  isStandalonePreview?: boolean;
  onGenerateComposition?: (
    userRequest: string, 
    mediaBinItems: MediaBinItem[], 
    modelType?: string,
    provider?: string,
    signal?: AbortSignal
  ) => Promise<boolean>;
  isGeneratingComposition?: boolean;
  // Props for conversational edit system
  currentComposition?: string; // Current TSX composition code
  // Props for adding generated images to media bin
  onAddMediaToBin?: (file: File) => Promise<void>;
  onAddGeneratedImage?: (item: MediaBinItem) => Promise<void>;
  // Props for updating media items (for upload status changes)
  onUpdateMediaItem?: (updatedItem: MediaBinItem) => void;
  // Error handling props
  generationError?: {
    hasError: boolean;
    errorMessage: string;
    errorStack?: string;
    brokenCode: string;
    originalRequest: string;
    canRetry: boolean;
  };
  onRetryFix?: () => Promise<boolean>;
  onClearError?: () => void;
  // Authentication
  getToken: GetTokenFn;
  // Provider selection
  initialEditProvider?: "gemini" | "claude";
  initialAgentProvider?: "gemini" | "gemini-3-low" | "gemini-3-high" | "claude" | "openai";
}

export function ChatBox({
  className = "",
  mediaBinItems,
  handleDropOnTrack,
  isMinimized = false,
  onToggleMinimize,
  messages,
  onMessagesChange,
  timelineState,
  isStandalonePreview = false,
  onGenerateComposition,
  isGeneratingComposition = false,
  currentComposition,
  onAddMediaToBin,
  onAddGeneratedImage,
  onUpdateMediaItem,
  generationError,
  onRetryFix,
  onClearError,
  getToken,
  initialEditProvider = "gemini",
  initialAgentProvider = "gemini",
}: ChatBoxProps) {
  const [inputValue, setInputValue] = useState("");
  const [showMentions, setShowMentions] = useState(false);
  const [showSendOptions, setShowSendOptions] = useState(false);
  const [mentionQuery, setMentionQuery] = useState("");
  const [selectedMentionIndex, setSelectedMentionIndex] = useState(0);
  const [cursorPosition, setCursorPosition] = useState(0);
  const [textareaHeight, setTextareaHeight] = useState(36); // Starting height for proper size
  
  // Keep a ref to the latest media bin items so async workflows can always access current state
  const mediaBinItemsRef = useRef<MediaBinItem[]>(mediaBinItems);
  
  // Update ref whenever prop changes
  useEffect(() => {
    mediaBinItemsRef.current = mediaBinItems;
  }, [mediaBinItems]);
  const [selectedModel, setSelectedModel] = useState<string>(initialAgentProvider); // AI model selection (for agent)
  const [selectedEditProvider, setSelectedEditProvider] = useState<string>(initialEditProvider); // Edit engine provider
  const [sendWithMedia, setSendWithMedia] = useState(false); // Track send mode
  const [mentionedItems, setMentionedItems] = useState<MediaBinItem[]>([]); // Store actual mentioned items
  const [collapsedMessages, setCollapsedMessages] = useState<Set<string>>(new Set()); // Track collapsed analysis results
  const [isInSynthLoop, setIsInSynthLoop] = useState(false); // Track when unified workflow is active
  const [previewItem, setPreviewItem] = useState<MediaBinItem | null>(null); // Track media being previewed

  // Note: Gemini upload removed - backend GCS storage handles everything now
  // Stock videos are uploaded directly to GCS with signed URLs during fetch

  // Helper to get authenticated headers
  const getAuthHeaders = useCallback(async () => {
    const token = await getToken();
    return {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    };
  }, [getToken]);

  // Initialize Conversational Synth with getToken for authenticated backend calls
  const [synth] = useState(() => new ConversationalSynth("dummy-api-key", getToken));
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const mentionsRef = useRef<HTMLDivElement>(null);
  const sendOptionsRef = useRef<HTMLDivElement>(null);
  // Controller used to cancel in-flight agent/analysis requests
  const abortControllerRef = useRef<AbortController | null>(null);
  // Ref to control whether unified workflow should continue (accessible from stop button)
  const continueWorkflowRef = useRef<boolean>(false);

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
      console.log("🔄 Retrying with existing conversation history");
      console.log("🔄 Current media bin items:", mediaBinItems.map(item => ({
        name: item.name,
        hasRemoteUrl: !!item.mediaUrlRemote,
        isUploading: item.isUploading
      })));
      // The message is already in the conversation history, just re-run the workflow
      handleConversationalMessage();
    }
  }, [mediaBinItems]);

  // Filter media bin items based on mention query
  const filteredMentions = mediaBinItems.filter((item) =>
    item.name.toLowerCase().includes(mentionQuery.toLowerCase())
  );

  // Handle input changes and @ mention detection
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    const cursorPos = e.target.selectionStart || 0;

    setInputValue(value);
    setCursorPosition(cursorPos);

    // Auto-resize textarea
    const textarea = e.target;
    textarea.style.height = "auto";
    const newHeight = Math.min(textarea.scrollHeight, 96); // max about 4 lines
    textarea.style.height = newHeight + "px";
    setTextareaHeight(newHeight);

    // Clean up mentioned items that are no longer in the text
    const mentionPattern = /@(\w+(?:\s+\w+)*)/g;
    const currentMentions = Array.from(value.matchAll(mentionPattern)).map(match => match[1]);
    setMentionedItems(prev => prev.filter(item => 
      currentMentions.some(mention => mention.toLowerCase() === item.name.toLowerCase())
    ));

    // Check for @ mentions
    const beforeCursor = value.slice(0, cursorPos);
    const lastAtIndex = beforeCursor.lastIndexOf("@");

    if (lastAtIndex !== -1) {
      const afterAt = beforeCursor.slice(lastAtIndex + 1);
      // Only show mentions if @ is at start or after whitespace, and no spaces after @
      const isValidMention =
        (lastAtIndex === 0 || /\s/.test(beforeCursor[lastAtIndex - 1])) &&
        !afterAt.includes(" ");

      if (isValidMention) {
        setMentionQuery(afterAt);
        setShowMentions(true);
        setSelectedMentionIndex(0);
      } else {
        setShowMentions(false);
      }
    } else {
      setShowMentions(false);
    }
  };

  // Insert mention into input
  const insertMention = (item: MediaBinItem) => {
    const beforeCursor = inputValue.slice(0, cursorPosition);
    const afterCursor = inputValue.slice(cursorPosition);
    const lastAtIndex = beforeCursor.lastIndexOf("@");

    const newValue =
      beforeCursor.slice(0, lastAtIndex) + `@${item.name} ` + afterCursor;
    setInputValue(newValue);
    setShowMentions(false);

    // Store the actual item reference for later use
    setMentionedItems(prev => {
      // Avoid duplicates
      if (!prev.find(existingItem => existingItem.id === item.id)) {
        return [...prev, item];
      }
      return prev;
    });

    // Focus back to input
    setTimeout(() => {
      inputRef.current?.focus();
      const newCursorPos = lastAtIndex + item.name.length + 2;
      inputRef.current?.setSelectionRange(newCursorPos, newCursorPos);
    }, 0);
  };

  // Batch probe handler - analyzes multiple videos in parallel
  const handleProbeRequestInternal = async (
    videos: Array<{ fileName: string; question: string }>,
    signal?: AbortSignal
  ): Promise<Message[]> => {
    console.log(`🔍 Executing batch probe request for ${videos.length} video(s)`);
    
    // Log all probes
    for (const video of videos) {
      await logProbeStart(video.fileName, video.question);
    }
    
    // Resolve all fileNames to URLs
    const resolvedVideos = await Promise.all(
      videos.map(async (video) => {
        const trimmedFileName = video.fileName.trim();
        let fileUrl = trimmedFileName;
        
        // Check if fileName is a URL (starts with http, https, gs://, or youtube)
        const isUrl = /^(https?:\/\/|gs:\/\/|youtube\.com|youtu\.be)/i.test(trimmedFileName);
        
        if (!isUrl) {
          // fileName is a name reference - look it up in media library
          console.log(`🔍 Resolving "${trimmedFileName}" from media library...`);
          const mediaItem = mediaBinItemsRef.current.find(item => item.name.trim() === trimmedFileName);
          
          if (mediaItem) {
            // Prefer remote URL over GCS URI for better MIME type detection
            fileUrl = mediaItem.mediaUrlRemote || mediaItem.gcsUri || '';
            console.log(`🔍 Resolved "${trimmedFileName}" → ${fileUrl}`);
            
            if (!fileUrl) {
              throw new Error(`Media item "${trimmedFileName}" has no URL available`);
            }
          } else {
            console.warn(`⚠️ Media item "${trimmedFileName}" not found in library`);
            console.warn(`⚠️ Available names:`, mediaBinItemsRef.current.map(item => `"${item.name.trim()}"`));
            throw new Error(`Media item "${trimmedFileName}" not found in library`);
          }
        }
        
        return {
          file_url: fileUrl,
          title: trimmedFileName,
          question: video.question // Include per-video question
        };
      })
    );
    
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(apiUrl('/api/v1/analysis/media/batch', true), {
        method: 'POST',
        headers,
        body: JSON.stringify({
          videos: resolvedVideos, // Each video now includes its own question
          max_concurrent: 4
        }),
        signal
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Batch analysis failed: ${response.status}`);
      }

      const result = await response.json();
      
      if (!result.success) {
        throw new Error('Batch analysis failed');
      }

      const aggregatedAnalysis = result.aggregated_analysis;
      
      // Log each video's analysis
      for (const videoResult of result.results) {
        if (videoResult.success && videoResult.analysis) {
          await logProbeAnalysis(videoResult.title || videoResult.file_url, videoResult.analysis);
        } else if (!videoResult.success) {
          await logProbeError(videoResult.title || videoResult.file_url, videoResult.error_message || 'Analysis failed');
        }
      }
      
      const responseMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: aggregatedAnalysis,
        isUser: false,
        timestamp: new Date(),
        isAnalysisResult: true,
        sender: 'tool'
      };

      // Immediately add to collapsed state so it appears collapsed from the start
      setCollapsedMessages(prev => {
        const newSet = new Set(prev);
        newSet.add(responseMessage.id);
        return newSet;
      });
      
      return [responseMessage];

    } catch (error) {
      console.error("❌ Batch probe analysis failed:", error);
      
      // Log errors for all videos
      for (const video of videos) {
        await logProbeError(video.fileName, error instanceof Error ? error.message : 'Unknown error');
      }
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `Failed to analyze ${videos.length} video(s). ${error instanceof Error ? error.message : 'Unknown error'}`,
        isUser: false,
        timestamp: new Date(),
        isSystemMessage: true,
        sender: 'tool',
        hasRetryButton: true,
        retryData: {
          originalMessage: `analyze ${videos.map(v => v.fileName).join(', ')}`
        }
      };
      return [errorMessage];
    }
  };  const handleProbeRequest = async (
    fileName: string, 
    question: string, 
    originalMessage: string, 
    conversationMessages: ConversationMessage[],
    synthContext: SynthContext
  ): Promise<Message[]> => {
    // Wrap single file into batch format for backward compatibility
    return handleProbeRequestInternal([{ fileName, question }]);
  };

  const analyzeMediaWithGemini = async (mediaFile: MediaBinItem, question: string, signal?: AbortSignal): Promise<string> => {
    // All media analysis now goes through the backend API
    // Backend handles videos, images, audio, and documents via Gemini
    
    console.log("🔍 Analyzing media with backend API:", {
      name: mediaFile.name,
      mediaUrlRemote: mediaFile.mediaUrlRemote,
      mediaUrlLocal: mediaFile.mediaUrlLocal,
      isUploading: mediaFile.isUploading,
      uploadProgress: mediaFile.uploadProgress,
      gcsUri: mediaFile.gcsUri
    });
    
    // Check if media file has been uploaded to GCS
    // Use GCS URI (gs://) for Vertex AI access, fallback to HTTPS URL
    const fileUrl = mediaFile.gcsUri || mediaFile.mediaUrlRemote;
    
    if (!fileUrl) {
      console.error("❌ No GCS URL available for media file:", mediaFile);
      
      // Provide specific error based on upload status
      if (mediaFile.isUploading) {
        throw new Error(`Media file "${mediaFile.name}" is currently uploading to cloud storage (${mediaFile.uploadProgress || 0}%). Please wait for upload to complete.`);
      } else {
        throw new Error(`Media file "${mediaFile.name}" was not uploaded to cloud storage. Please delete and re-upload the file.`);
      }
    }

    try {
      // Call backend media analysis endpoint with GCS URI
      // Backend uses gs:// URI with Vertex AI for direct GCS access
      console.log("🔗 Sending file URL to backend:", fileUrl);
      const headers = await getAuthHeaders();
      const response = await fetch(apiUrl('/api/v1/analysis/media', true), {
        method: 'POST',
        headers,
        body: JSON.stringify({
          file_url: fileUrl,  // GCS URI (gs://bucket/path) for Vertex AI
          question: question,
          temperature: 0.1
        }),
        signal
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error_message || `Backend analysis failed: ${response.status}`);
      }

      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.error_message || 'Media analysis failed');
      }

      console.log("✅ Backend analysis complete:", result.model_used);
      return result.analysis;

    } catch (error) {
      console.error("❌ Backend media analysis failed:", error);
      throw error;
    }
  };

  // Simple internal handlers that just execute actions (no nested synth calls)
  const handleGenerateRequestInternal = async (
    prompt: string,
    suggestedName: string,
    description: string,
    contentType: 'image' | 'video' | 'logo' | 'audio' = 'image', // Add audio content type
    seedImageFileName?: string, // Add seed image parameter for video generation
    voiceSettings?: { voice_id?: string; language_code?: string; speaking_rate?: number; pitch?: number }, // Voice settings for audio
    generatedItemsArray?: MediaBinItem[], // Optional array to track generated items
    signal?: AbortSignal
  ): Promise<{ messages: Message[], newMediaItem: MediaBinItem | null }> => {
    console.log("🎨 Executing generation request:", { prompt, suggestedName, description, contentType, seedImageFileName, voiceSettings });
    
    try {
      // Call the backend generation API for both image and video
      console.log(`� Calling backend ${contentType} generation API for:`, prompt);
      
      const requestBody: any = {
        content_type: contentType,
        prompt: prompt,
      };

      // Add video-specific parameters
      if (contentType === 'video') {
        requestBody.aspect_ratio = "16:9";
        requestBody.resolution = "720p";
        
        // Handle seed image for video generation (universal pattern: name → URL resolution)
        if (seedImageFileName) {
          // Find the seed image in media library by name
          const seedImage = mediaBinItems.find((item: MediaBinItem) => item.name === seedImageFileName);
          if (seedImage) {
            // Resolve name to URL (prefer remote, fallback to local)
            const imageUrl = seedImage.mediaUrlRemote || seedImage.mediaUrlLocal;
            if (imageUrl) {
              // Send URL to backend (backend will download it)
              requestBody.reference_image_url = imageUrl;
              console.log(`🖼️ Resolved seed image "${seedImageFileName}" → ${imageUrl.substring(0, 60)}...`);
            } else {
              console.warn(`⚠️ Seed image "${seedImageFileName}" has no valid URL`);
            }
          } else {
            console.warn(`⚠️ Seed image "${seedImageFileName}" not found in media library`);
            console.warn(`📋 Available media:`, mediaBinItems.map(item => item.name));
          }
        }
      }

      // Add audio-specific parameters
      if (contentType === 'audio' && voiceSettings) {
        requestBody.voice_settings = voiceSettings;
      }

      const headers = await getAuthHeaders();
      const response = await fetch(apiUrl('/api/v1/media/generate', true), {
        method: 'POST',
        headers,
        body: JSON.stringify(requestBody),
        signal
      });

      if (!response.ok) {
        throw new Error(`Generation failed: ${response.status} ${response.statusText}`);
      }

      const result = await response.json();
      console.log(`🎨 ${contentType} generation result:`, result);

      if (!result.success) {
        throw new Error(result.error_message || 'Generation failed');
      }

      // Handle async video generation (polling required)
      let generatedAsset;
      
      if (result.status === 'processing' && result.operation_id) {
        // Video generation is async - poll for completion
        console.log(`🎥 Video generation started, polling operation: ${result.operation_id}`);
        
        const maxAttempts = 120; // 10 minutes max
        let attempts = 0;
        let delay = 5000; // Start with 5 seconds
        
        while (attempts < maxAttempts) {
          // Wait before polling
          await new Promise(resolve => setTimeout(resolve, delay));
          
          // Check status
          const statusHeaders = await getAuthHeaders();
          const statusResponse = await fetch(
            apiUrl(`/api/v1/media/status/${encodeURIComponent(result.operation_id)}`, true),
            {
              method: 'GET',
              headers: statusHeaders,
              signal
            }
          );
          
          if (!statusResponse.ok) {
            throw new Error(`Status check failed: ${statusResponse.status}`);
          }
          
          const statusResult = await statusResponse.json();
          console.log(`🎥 Video generation status (attempt ${attempts + 1}):`, statusResult.status);
          
          if (statusResult.status === 'completed') {
            generatedAsset = statusResult.generated_asset;
            console.log(`✅ Video generation completed:`, generatedAsset);
            break;
          } else if (statusResult.status === 'failed') {
            throw new Error(statusResult.error_message || 'Video generation failed');
          }
          
          // Still processing - continue polling with exponential backoff
          attempts++;
          delay = Math.min(delay * 1.2, 30000); // Cap at 30 seconds
        }
        
        if (!generatedAsset) {
          throw new Error('Video generation timed out after 10 minutes');
        }
      } else {
        // Image generation completes immediately
        generatedAsset = result.generated_asset;
      }
      
      console.log(`🎨 Generated ${contentType} asset:`, generatedAsset);
      console.log(`🎨 Generated file URL:`, generatedAsset.file_url);

      // Create the MediaBinItem for the generated content
      // Make sure the URL points to the correct FastAPI server
      const fastApiBaseUrl = getApiBaseUrl(true); // true for FastAPI
      const mediaUrl = generatedAsset.file_url.startsWith('http') 
        ? generatedAsset.file_url 
        : `${fastApiBaseUrl}${generatedAsset.file_url}`;
      
      console.log(`🎨 Final ${contentType} URL:`, mediaUrl);

      // Use name from backend (already unique)
      const name = generatedAsset.name;

      const newMediaItem: MediaBinItem = {
        id: generateUUID(),
        name,
        title: name,
        mediaType: contentType === 'video' ? "video" : contentType === 'audio' ? "audio" : "image",
        mediaUrlLocal: null,
        mediaUrlRemote: mediaUrl,
        gcsUri: generatedAsset.gcs_uri,
        media_width: generatedAsset.width,
        media_height: generatedAsset.height,
        durationInSeconds: (contentType === 'video' || contentType === 'audio') ? (generatedAsset.duration_seconds || 8.0) : 0,
        text: null,
        isUploading: false,
        uploadProgress: null,
        upload_status: 'uploaded',
        gemini_file_id: null,
        left_transition_id: null,
        right_transition_id: null,
      };

      console.log(`🎨 Created ${contentType} MediaBinItem:`, newMediaItem);

      // Add the generated content to the media bin
      if (onAddGeneratedImage) {
        await onAddGeneratedImage(newMediaItem);

        // Sync ref immediately so in-flight workflows see the new asset
        mediaBinItemsRef.current = [...mediaBinItemsRef.current, newMediaItem];
        console.log(`📦 Immediately added ${newMediaItem.name} to ref. Ref now has ${mediaBinItemsRef.current.length} items`);
      }

      // Create success message that clearly indicates completion
      const generationMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `Successfully generated ${contentType}: ${name}. The ${contentType} has been added to your media library.`,
        isUser: false,
        sender: 'tool',
        timestamp: new Date(),
        isSystemMessage: true,
      };

      return { messages: [generationMessage], newMediaItem };

    } catch (error) {
      console.error(`${contentType} generation failed:`, error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `Failed to generate ${contentType}: ${error instanceof Error ? error.message : 'Unknown error'}`,
        isUser: false,
        sender: 'tool',
        timestamp: new Date(),
        isSystemMessage: true,
      };
      return { messages: [errorMessage], newMediaItem: null };
    }
  };

  // Simple internal handler for fetching stock videos (dummy implementation)
  const handleFetchRequestInternal = async (
    provider: 'pexels' | 'shutterstock',
    query: string,
    count: number,
    signal?: AbortSignal
  ): Promise<Message[]> => {
    console.log("🎬 Executing stock video fetch request:", { provider, query, count });
    
    try {
      // Debug: log what we're about to send
      console.log("🔍 About to call backend with query:", query);
      console.log("🔍 Request count parameter:", count);
      console.log("🔍 Request body:", { 
        query: query, 
        media_type: "video",
        orientation: "landscape",
        max_results: count || 3,
        per_page: 50
      });
      
      // Debug: Log the full URL being called
      const fetchUrl = apiUrl("/api/v1/stock/search", true);
      console.log("🔍 Full fetch URL:", fetchUrl);
      
      // Call the actual backend API to fetch stock videos
      const headers = await getAuthHeaders();
      const response = await fetch(fetchUrl, {
        method: "POST",
        headers,
        body: JSON.stringify({
          query: query,
          media_type: "video",
          orientation: "landscape",
          max_results: count || 3,
          per_page: 50
        }),
        signal
      });

      if (!response.ok) {
        throw new Error(`API call failed: ${response.status} ${response.statusText}`);
      }

      const result = await response.json();
      console.log("🎬 Backend fetch result:", result);
      console.log("🎬 Number of items returned:", result.items?.length || 0);
      console.log("🎬 Total results from provider:", result.total_results);
      console.log("🎬 AI curation explanation:", result.ai_curation_explanation);

      if (!result.success || !result.items || result.items.length === 0) {
        throw new Error(result.error_message || "No videos found");
      }

      // Transform backend response to UI format
      const videoOptions = result.items.map((item: any, index: number) => ({
        id: item.id,
        title: `Option ${index + 1}`,
        duration: item.duration ? `${item.duration}s` : 'N/A',
        description: `${item.quality?.toUpperCase() || 'HD'} quality - ${item.width}x${item.height} - by ${item.creator_name}`,
        thumbnailUrl: item.preview_url,
        downloadUrl: item.storage_url,
        pexelsUrl: item.provider_url,
        width: item.width,
        height: item.height,
        durationInSeconds: item.duration
      }));

      // Add all fetched videos to the media library automatically
      if (onAddGeneratedImage) {
        // First, add all media items to the bin
        const mediaItemsToUpload: Array<{mediaItem: MediaBinItem, item: any, videoUrl: string}> = [];
        
        for (let index = 0; index < result.items.length; index++) {
          const item = result.items[index];
          console.log(`🎬 [VIDEO ${index}] Processing video:`, {
            id: item.id,
            idType: typeof item.id,
            creator: item.creator_name,
            quality: item.quality,
            storage_url: item.storage_url
          });
          
          // storage_url is already a full GCS URL from backend
          const videoUrl = item.storage_url;
            
          console.log(`🎬 [VIDEO ${index}] Video URL: ${videoUrl}`);

          // Use name from backend (already unique)
          const name = item.name;

          // Create MediaBinItem for each video
          const mediaItem: MediaBinItem = {
            id: generateUUID(),
            name,
            title: name,
            mediaType: "video",
            mediaUrlLocal: null,
            mediaUrlRemote: videoUrl,
            media_width: item.width,
            media_height: item.height,
            durationInSeconds: item.duration,
            text: null,
            isUploading: false,
            uploadProgress: null,
            upload_status: 'uploaded',
            gemini_file_id: null,
            left_transition_id: null,
            right_transition_id: null,
          };

          console.log(`🎬 [VIDEO ${index}] Created MediaBinItem:`, {
            mediaItemId: mediaItem.id,
            mediaItemName: mediaItem.name,
            itemId: item.id,
            remoteUrl: mediaItem.mediaUrlRemote
          });
          
          // Update parent state (async) AND ref (immediate) for consistent state across iterations
          await onAddGeneratedImage(mediaItem);
          mediaBinItemsRef.current = [...mediaBinItemsRef.current, mediaItem];
          console.log(`📦 Immediately added ${mediaItem.name} to ref. Ref now has ${mediaBinItemsRef.current.length} items`);
        }
        
        // Note: All videos are already uploaded to GCS by the backend
        // No separate Gemini upload needed
      }

      // Create the selection message with real video thumbnails
      const videoOptionsMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `I found ${result.items.length} stock videos for "${query}". All videos have been added to your media library. Click to preview:`,
        isUser: false,
        sender: 'tool',
        timestamp: new Date(),
        isSystemMessage: false,
        isVideoSelection: true,
        videoOptions: videoOptions,
      };

      return [videoOptionsMessage];

    } catch (error) {
      console.error("Stock video fetch failed:", error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `Failed to fetch stock videos: ${error instanceof Error ? error.message : 'Unknown error'}`,
        isUser: false,
        sender: 'tool',
        timestamp: new Date(),
        isSystemMessage: true,
      };
      return [errorMessage];
    }
  };

  const handleConversationalMessage = async (): Promise<void> => {
    await handleConversationalMessageWithUpdatedMessages(messages);
  };

  const handleConversationalMessageWithUpdatedMessages = async (currentMessages: Message[]): Promise<void> => {
    // Get the last user message from conversation history for logging
    const lastUserMessage = [...currentMessages]
      .reverse()
      .find(m => (m.sender ?? (m.isUser ? 'user' : 'assistant')) === 'user');
    const messageContent = lastUserMessage?.content || '';
    
    await logUserMessage(messageContent, mentionedItems.map(item => item.name));
    console.log("🧠 Processing conversational message with unified workflow:", messageContent);

    // Initialize unified workflow state
    // We maintain a local history that is perfectly synchronous with what we want the agent to see
    // This ensures the agent sees its own actions and doesn't repeat them
    let conversationHistory: Message[] = [...currentMessages];
    
    let continueWorkflow = true;
    let iterationCount = 0;
    const MAX_ITERATIONS = 20; // Prevent infinite loops
    
    // Create AbortController for cancellation
    const abortController = new AbortController();
    abortControllerRef.current = abortController;
    
    // Reset the continuation control ref
    continueWorkflowRef.current = true;
    
    // Start the loading indicator for the entire workflow
    setIsInSynthLoop(true);

    // Helper to add message to both UI and local history sequentially
    const addMessageToHistory = (message: Message) => {
        // Add to local history for the agent's next turn
        conversationHistory.push(message);
        // Add to UI immediately
        onMessagesChange(prev => [...prev, message]);
    };
    
    try {
      // Unified workflow loop: synth → execute → update history → repeat
      while (continueWorkflow && continueWorkflowRef.current && iterationCount < MAX_ITERATIONS) {
        iterationCount++;
        console.log(`🔄 Unified workflow iteration ${iterationCount}`);
      
        try {
            // Prepare context for the synth
            // We map the Message objects to ConversationMessage objects expected by the synth
            const conversationMessages: ConversationMessage[] = conversationHistory.map(msg => ({
              id: msg.id,
              content: msg.content,
              isUser: msg.isUser,
              timestamp: msg.timestamp,
              sender: msg.sender ?? (msg.isUser ? 'user' : 'assistant')
            }));

            // Build synth context with latest state using ref (always current)
            const currentMediaBin = mediaBinItemsRef.current;
            const synthContext: SynthContext = {
                messages: conversationMessages,
                currentComposition: currentComposition ? JSON.parse(currentComposition) : undefined,
                mediaLibrary: currentMediaBin,
                compositionDuration: undefined,
                provider: selectedModel
            };

            console.log(`📚 Media library has ${currentMediaBin.length} items for iteration ${iterationCount}`);
            await logSynthCall("conversation_analysis", synthContext);
            
            // Get the next action from the agent
            const synthResponse = await synth.processMessage(synthContext, abortController.signal);
            await logSynthResponse(synthResponse);
            
            console.log(`🎯 Synth response type: ${synthResponse.type}`);

            // Execute the action and update history
            // We pass addMessageToHistory so the action can append messages sequentially
            const shouldContinue = await executeResponseAction(
                synthResponse, 
                synthContext, 
                addMessageToHistory, 
                abortController.signal
            );

            continueWorkflow = shouldContinue;

        } catch (error) {
            console.error(`❌ Unified workflow iteration ${iterationCount} failed:`, error);
            await logSynthResponse({ error: error instanceof Error ? error.message : String(error) });
            
            const errorMessage: Message = {
                id: (Date.now() + iterationCount).toString(),
                content: "I'm having trouble processing your request. Let me try a different approach.",
                isUser: false,
                sender: 'system',
                timestamp: new Date(),
                isSystemMessage: true
            };
            addMessageToHistory(errorMessage);
            continueWorkflow = false;
        }
      }

      if (iterationCount >= MAX_ITERATIONS) {
          console.warn("⚠️ Unified workflow hit max iterations limit");
          const maxIterationMessage: Message = {
            id: Date.now().toString(),
            content: "I've completed several steps but need to pause here. How can I help you next?",
            isUser: false,
            sender: 'system',
            timestamp: new Date(),
            isSystemMessage: true
          };
          addMessageToHistory(maxIterationMessage);
      }

      await logWorkflowComplete();

    } catch (error) {
      console.error("❌ Unified workflow failed:", error);
      if (error instanceof Error && error.name === 'AbortError') {
        console.log("🛑 Workflow was cancelled by user");
        const cancelMessage: Message = {
          id: Date.now().toString(),
          content: "Workflow cancelled.",
          isUser: false,
          sender: 'system',
          timestamp: new Date(),
          isSystemMessage: true
        };
        onMessagesChange(prevMessages => [...prevMessages, cancelMessage]);
      } else {
        const errorMessage: Message = {
          id: Date.now().toString(),
          content: "I'm having trouble processing your request. Please try again.",
          isUser: false,
          sender: 'system',
          timestamp: new Date(),
          isSystemMessage: true
        };
        onMessagesChange(prevMessages => [...prevMessages, errorMessage]);
      }
    } finally {
      setIsInSynthLoop(false);
      abortControllerRef.current = null;
      continueWorkflowRef.current = false;
    }
  };

  // Execute the appropriate action based on response type
  // Returns true if workflow should continue, false if it should halt
  const executeResponseAction = async (
    synthResponse: SynthResponse,
    synthContext: SynthContext,
    addMessage: (msg: Message) => void,
    signal?: AbortSignal
  ): Promise<boolean> => {
    console.log(`🎬 Executing action for response type: ${synthResponse.type}`);
    
    if (synthResponse.type === 'info') {
        // Info response - just display and continue
        const message: Message = {
            id: generateUUID(),
            content: synthResponse.content,
            isUser: false,
            timestamp: new Date(),
            sender: 'assistant'
        };
        addMessage(message);
        return true; // Continue loop
    }
    
    if (synthResponse.type === 'chat') {
        // Chat response - display and HALT
        const message: Message = {
            id: generateUUID(),
            content: synthResponse.content,
            isUser: false,
            timestamp: new Date(),
            sender: 'assistant'
        };
        addMessage(message);
        return false; // HALT loop
    }

    if (synthResponse.type === 'fetch') {
        // 1. Announce action
        const announcement: Message = {
            id: generateUUID(),
            content: `Fetching stock videos: ${synthResponse.query}`,
            isUser: false,
            timestamp: new Date(),
            isSystemMessage: true,
            sender: 'assistant'
        };
        addMessage(announcement);

        // 2. Execute action
        const results = await handleFetchRequestInternal('pexels', synthResponse.query!, 3, signal);
        
        // 3. Add results
        results.forEach(msg => addMessage(msg));
        
        return true; // Continue loop
    }

    if (synthResponse.type === 'generate') {
        // 1. Announce action
        const contentTypeText = synthResponse.content_type || 'image';
        const announcement: Message = {
            id: generateUUID(),
            content: `Generating ${contentTypeText}: ${synthResponse.prompt}`,
            isUser: false,
            timestamp: new Date(),
            isSystemMessage: true,
            sender: 'assistant'
        };
        addMessage(announcement);

        // 2. Execute action
        const result = await handleGenerateRequestInternal(
            synthResponse.prompt!,
            synthResponse.suggestedName!,
            synthResponse.content,
            synthResponse.content_type || 'image',
            synthResponse.seedImageFileName,
            synthResponse.voice_settings,
            undefined,
            signal
        );

        // 3. Add results
        // Note: handleGenerateRequestInternal already updates mediaBinItemsRef if successful
        result.messages.forEach(msg => addMessage(msg));

        return true; // Continue loop
    }

    if (synthResponse.type === 'probe') {
        // 1. Announce action
        const filesToAnalyze = synthResponse.files || 
            (synthResponse.fileName ? [{ fileName: synthResponse.fileName, question: synthResponse.question || 'Describe what you see in this media.' }] : []);
        
        const fileNames = filesToAnalyze.map(f => f.fileName).join(', ');
        const announcement: Message = {
            id: generateUUID(),
            content: `Analyzing ${filesToAnalyze.length} file(s): ${fileNames}`,
            isUser: false,
            timestamp: new Date(),
            isSystemMessage: true,
            sender: 'assistant'
        };
        addMessage(announcement);

        // 2. Execute action
        const results = await handleProbeRequestInternal(filesToAnalyze, signal);

        // 3. Add results
        results.forEach(msg => addMessage(msg));

        return true; // Continue loop
    }

    if (synthResponse.type === 'edit') {
        // 1. Announce action
        const announcement: Message = {
            id: generateUUID(),
            content: `Applying edits...`,
            isUser: false,
            timestamp: new Date(),
            isSystemMessage: true,
            sender: 'assistant'
        };
        addMessage(announcement);

        // 2. Execute action
        console.log("🎬 Executing edit:", synthResponse.content);
        await logEditExecution(synthResponse.content);
        
        let success = false;
        if (onGenerateComposition) {
            success = await onGenerateComposition(
                synthResponse.content, 
                mediaBinItemsRef.current, 
                selectedModel,
                selectedEditProvider,
                signal
            );
        }
        await logEditResult(success);
        
        // 3. Result
        const resultMessage: Message = {
            id: generateUUID(),
            content: success ? "Edit implemented successfully!" : "Failed to implement the edit. Please try again.",
            isUser: false,
            timestamp: new Date(),
            isSystemMessage: true,
            sender: 'tool'
        };
        addMessage(resultMessage);
        
        return true; // Continue loop
    }

    // Fallback for unknown types
    console.log("❓ Executing fallback for unknown type:", synthResponse.type);
    const fallbackMsg: Message = {
        id: generateUUID(),
        content: synthResponse.content,
        isUser: false,
        timestamp: new Date(),
        sender: 'assistant'
    };
    addMessage(fallbackMsg);
    return true;
  };

  const handleSendMessage = async (includeAllMedia = false) => {
    if (!inputValue.trim()) return;

    let messageContent = inputValue.trim();
    let itemsToSend = mentionedItems;

    // If sending with all media, include all media items
    if (includeAllMedia && mediaBinItems.length > 0) {
      const mediaList = mediaBinItems.map((item) => `@${item.name}`).join(" ");
      messageContent = `${messageContent} ${mediaList}`;
      // Add all media items to the items to send
      itemsToSend = [...mentionedItems, ...mediaBinItems.filter(item => 
        !mentionedItems.find(mentioned => mentioned.id === item.id)
      )];
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      content: messageContent,
      isUser: true,
      timestamp: new Date(),
    };

    // Update messages state
    const updatedMessages = [...messages, userMessage];
    onMessagesChange(prevMessages => [...prevMessages, userMessage]);
    setInputValue("");
    setMentionedItems([]); // Clear mentioned items after sending

    // Reset textarea height
    if (inputRef.current) {
      inputRef.current.style.height = "36px"; // Back to normal height
      setTextareaHeight(36);
    }

    try {
      // Check if we're in standalone preview mode - use conversational synth
      if (isStandalonePreview) {
        console.log("🎬 Standalone preview mode - using conversational synth");
        
        // Pass the updated messages directly to avoid async state issues
        await handleConversationalMessageWithUpdatedMessages(updatedMessages);
        
        return;
      }

      console.log("📹 Using timeline-based AI (not standalone mode)");
      // Original timeline-based AI functionality
      // Use the stored mentioned items to get their IDs
      const mentionedScrubberIds = itemsToSend.map(item => item.id);

      // Make API call to the backend
      const token = await getToken();
      // TODO: Update this to use the new agent endpoint properly
      const response = await axios.post(apiUrl("/api/v1/agent/chat", true), {
        message: messageContent,
        mentioned_scrubber_ids: mentionedScrubberIds,
        timeline_state: timelineState,
        mediabin_items: mediaBinItems,
      }, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });

      const functionCallResponse = response.data;
      let aiResponseContent = "";

      // Handle the function call based on function_name
      if (functionCallResponse.function_call) {
        const { function_call } = functionCallResponse;
        
        try {
          if (function_call.function_name === "LLMAddScrubberToTimeline") {
            // Find the media item by ID
            const mediaItem = mediaBinItems.find(
              item => item.id === function_call.scrubber_id
            );

            if (!mediaItem) {
              aiResponseContent = `❌ Error: Media item with ID "${function_call.scrubber_id}" not found in the media bin.`;
            } else {
              // Execute the function
              llmAddScrubberToTimeline(
                function_call.scrubber_id,
                mediaBinItems,
                function_call.track_id,
                function_call.drop_left_px,
                handleDropOnTrack
              );

              aiResponseContent = `✅ Successfully added "${mediaItem.name}" to ${function_call.track_id} at position ${function_call.drop_left_px}px.`;
            }
          } else {
            aiResponseContent = `❌ Unknown function: ${function_call.function_name}`;
          }
        } catch (error) {
          aiResponseContent = `❌ Error executing function: ${
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

      onMessagesChange(prevMessages => [...prevMessages, userMessage, aiMessage]);
    } catch (error) {
      console.error("Error calling AI API:", error);
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `❌ Sorry, I encountered an error while processing your request. Please try again.`,
        isUser: false,
        sender: 'system',
        timestamp: new Date(),
      };
      
      onMessagesChange(prevMessages => [...prevMessages, userMessage, errorMessage]);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (showMentions && filteredMentions.length > 0) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedMentionIndex((prev) =>
          prev < filteredMentions.length - 1 ? prev + 1 : 0
        );
        return;
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedMentionIndex((prev) =>
          prev > 0 ? prev - 1 : filteredMentions.length - 1
        );
        return;
      }
      if (e.key === "Enter") {
        e.preventDefault();
        insertMention(filteredMentions[selectedMentionIndex]);
        return;
      }
      if (e.key === "Escape") {
        e.preventDefault();
        setShowMentions(false);
        return;
      }
    }

    if (e.key === "Enter") {
      if (e.shiftKey) {
        // Allow default behavior for Shift+Enter (new line)
        return;
      } else {
        // Send message on Enter
        e.preventDefault();
        handleSendMessage(sendWithMedia);
      }
    }
  };

  const toggleMessageCollapsed = (messageId: string) => {
    setCollapsedMessages(prev => {
      const newSet = new Set(prev);
      if (newSet.has(messageId)) {
        newSet.delete(messageId);
      } else {
        newSet.add(messageId);
      }
      return newSet;
    });
  };

  const formatMessageText = (text: string) => {
    // Simple markdown-like formatting
    return text
      .split(/(\*\*\*[^*]+\*\*\*|\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|^---+$|^#{1,6}\s+.+$)/gm)
      .map((part, index) => {
        if (part.startsWith('***') && part.endsWith('***')) {
          // Bold italic
          return <strong key={index} className="font-bold italic">{part.slice(3, -3)}</strong>;
        } else if (part.startsWith('**') && part.endsWith('**')) {
          // Bold
          return <strong key={index} className="font-bold">{part.slice(2, -2)}</strong>;
        } else if (part.startsWith('*') && part.endsWith('*')) {
          // Italic
          return <em key={index} className="italic">{part.slice(1, -1)}</em>;
        } else if (part.startsWith('`') && part.endsWith('`')) {
          // Code
          return <code key={index} className="bg-gray-200 dark:bg-gray-700 px-1 py-0.5 rounded text-xs font-mono">{part.slice(1, -1)}</code>;
        } else if (/^---+$/.test(part.trim())) {
          // Horizontal rule
          return <hr key={index} className="my-2 border-gray-300 dark:border-gray-600" />;
        } else if (/^#{1,6}\s+/.test(part)) {
          // Headings
          const level = part.match(/^(#{1,6})/)?.[1].length || 1;
          const content = part.replace(/^#{1,6}\s+/, '');
          if (level === 1) {
            return <h1 key={index} className="text-lg font-bold mt-2 mb-1">{content}</h1>;
          } else if (level === 2) {
            return <h2 key={index} className="text-base font-bold mt-2 mb-1">{content}</h2>;
          } else if (level === 3) {
            return <h3 key={index} className="text-sm font-semibold mt-1 mb-1">{content}</h3>;
          } else {
            return <h4 key={index} className="text-sm font-medium mt-1 mb-1">{content}</h4>;
          }
        } else {
          // Regular text
          return part;
        }
      });
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

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

      {/* Provider Selectors */}
      <div className="border-b border-border/50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-3 py-2">
        <div className="flex items-center gap-4">
          {/* Edit Engine Provider */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Edit Engine:</span>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm" className="h-6 text-xs">
                  {selectedEditProvider === "gemini" ? "Gemini" : "Claude"}
                  <ChevronDown className="w-3 h-3 ml-1" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" side="bottom" className="w-32">
                <DropdownMenuItem 
                  onClick={() => setSelectedEditProvider("gemini")}
                  className="text-xs"
                >
                  Gemini
                </DropdownMenuItem>
                <DropdownMenuItem 
                  onClick={() => setSelectedEditProvider("claude")}
                  className="text-xs"
                >
                  Claude
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
          
          {/* Agent Provider */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Agent:</span>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm" className="h-6 text-xs">
                  {selectedModel === "gemini" 
                    ? "Gemini 2.5" 
                    : selectedModel === "gemini-3-low"
                    ? "Gemini 3 Low"
                    : selectedModel === "gemini-3-high"
                    ? "Gemini 3 High"
                    : selectedModel === "claude" 
                    ? "Claude" 
                    : "GPT-4.1"}
                  <ChevronDown className="w-3 h-3 ml-1" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" side="bottom" className="w-32">
                <DropdownMenuItem 
                  onClick={() => setSelectedModel("gemini")}
                  className="text-xs"
                >
                  Gemini 2.5
                </DropdownMenuItem>
                <DropdownMenuItem 
                  onClick={() => setSelectedModel("gemini-3-low")}
                  className="text-xs"
                >
                  Gemini 3 Low
                </DropdownMenuItem>
                <DropdownMenuItem 
                  onClick={() => setSelectedModel("gemini-3-high")}
                  className="text-xs"
                >
                  Gemini 3 High
                </DropdownMenuItem>
                <DropdownMenuItem 
                  onClick={() => setSelectedModel("claude")}
                  className="text-xs"
                >
                  Claude
                </DropdownMenuItem>
                <DropdownMenuItem 
                  onClick={() => setSelectedModel("openai")}
                  className="text-xs"
                >
                  GPT-4.1
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 flex flex-col">
        {messages.length === 0 ? (
          // Default clean state - Copilot style
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
                <kbd className="px-1.5 py-0.5 text-xs bg-muted rounded">
                  Enter
                </kbd>
                <span>to send</span>
              </div>
              <div className="flex items-center gap-2">
                <kbd className="px-1.5 py-0.5 text-xs bg-muted rounded">
                  Shift
                </kbd>
                <span>+</span>
                <kbd className="px-1.5 py-0.5 text-xs bg-muted rounded">
                  Enter
                </kbd>
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
                                const success = await onRetryFix();
                                if (!success) {
                                  console.error("Retry failed");
                                }
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
                message.isSystemMessage ? (
                  // Render system messages as raw text
                  <div key={message.id} className="px-3 py-1 text-xs text-muted-foreground">
                    {message.content}
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
                                {formatMessageText(message.content)}
                              </p>
                            )}
                          </div>
                        ) : (
                          <p className={`leading-relaxed break-words overflow-wrap-anywhere ${
                            message.isExplanationMode
                              ? "text-green-800 dark:text-green-200"
                              : ""
                          }`}>
                            {formatMessageText(message.content)}
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
                                  // Generate unique name from video title (use ref for latest state)
                                  const title = video.title;
                                  const name = generateUniqueName(title, mediaBinItemsRef.current);

                                  // Convert video to MediaBinItem format for preview
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
                                  {/* Video Thumbnail - Fixed size */}
                                  <div className="flex-shrink-0">
                                    <img
                                      src={video.thumbnailUrl}
                                      alt={video.title}
                                      className="w-16 h-9 object-cover rounded border bg-gray-100 dark:bg-gray-800 block"
                                    />
                                  </div>
                                  {/* Video Info - Constrained */}
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

              {/* Simple loading indicator while in synth loop */}
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

              {/* Invisible element to scroll to */}
              <div ref={messagesEndRef} />
            </div>

            {/* Loading indicator removed - clean UI */}

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
                      handleSendMessage(false);
                    }}
                  >
                    <span>Send</span>
                    <span className="text-xs text-muted-foreground font-mono">
                      Enter
                    </span>
                  </div>
                  <div
                    className="px-3 py-2 text-xs cursor-pointer hover:bg-muted rounded flex items-center justify-between"
                    onClick={() => {
                      setSendWithMedia(true);
                      setShowSendOptions(false);
                      handleSendMessage(true);
                    }}
                  >
                    <span>Send with all Media</span>
                  </div>
                  <div
                    className="px-3 py-2 text-xs cursor-pointer hover:bg-muted rounded flex items-center justify-between"
                    onClick={() => {
                      // Clear current messages and send to new chat
                      onMessagesChange(() => []);
                      setShowSendOptions(false);
                      handleSendMessage(false);
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
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage(sendWithMedia);
                  }
                }}
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
                    onClick={() => {
                      console.log("⏹️ User clicked stop button - cancelling workflow");
                      continueWorkflowRef.current = false;
                      abortControllerRef.current?.abort();
                    }}
                    title="Stop agent workflow"
                  >
                    <X className="h-3 w-3" />
                  </Button>
                ) : (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0 text-primary hover:text-primary/80 hover:bg-primary/10"
                    onClick={() => handleSendMessage(sendWithMedia)}
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

      {/* Media Preview Modal - Using MediaBin style */}
      {previewItem && (
        <div 
          className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[60]"
          onClick={() => setPreviewItem(null)}
        >
          <div 
            className="bg-card border border-border rounded-lg shadow-2xl max-w-4xl max-h-[90vh] w-full mx-4 overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
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
                        {previewItem.media_width} × {previewItem.media_height}
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

            {/* Preview Content */}
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