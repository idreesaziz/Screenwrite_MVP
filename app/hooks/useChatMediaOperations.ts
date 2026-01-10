import { useCallback } from "react";
import type { MediaBinItem } from "~/components/editor/timeline/types";
import type { Message } from "~/types/chat";
import { apiUrl, getApiBaseUrl } from "~/lib/api";
import { generateUUID } from "~/lib/uuid";

export interface UseChatMediaOperationsOptions {
  getAuthHeaders: () => Promise<Record<string, string>>;
  mediaBinItemsRef: React.MutableRefObject<MediaBinItem[]>;
  mediaBinItems: MediaBinItem[];
  onAddGeneratedImage?: (mediaItem: MediaBinItem) => Promise<void>;
  setCollapsedMessages: React.Dispatch<React.SetStateAction<Set<string>>>;
}

export interface UseChatMediaOperationsReturn {
  probeMedia: (
    videos: Array<{ fileName: string; question: string }>,
    signal?: AbortSignal
  ) => Promise<Message[]>;
  generateMedia: (
    prompt: string,
    suggestedName: string,
    description: string,
    contentType?: 'image' | 'video' | 'logo' | 'audio',
    seedImageFileName?: string,
    voiceSettings?: { voice_id?: string; language_code?: string; speaking_rate?: number; pitch?: number },
    signal?: AbortSignal
  ) => Promise<{ messages: Message[]; newMediaItem: MediaBinItem | null }>;
  fetchStockVideos: (
    provider: 'pexels' | 'shutterstock',
    query: string,
    count: number,
    signal?: AbortSignal
  ) => Promise<Message[]>;
}

export function useChatMediaOperations({
  getAuthHeaders,
  mediaBinItemsRef,
  mediaBinItems,
  onAddGeneratedImage,
  setCollapsedMessages,
}: UseChatMediaOperationsOptions): UseChatMediaOperationsReturn {

  // Batch probe handler - analyzes multiple videos in parallel
  const probeMedia = useCallback(async (
    videos: Array<{ fileName: string; question: string }>,
    signal?: AbortSignal
  ): Promise<Message[]> => {
    // Resolve all fileNames to URLs
    const resolvedVideos = await Promise.all(
      videos.map(async (video) => {
        const trimmedFileName = video.fileName.trim();
        let fileUrl = trimmedFileName;
        
        const isUrl = /^(https?:\/\/|gs:\/\/|youtube\.com|youtu\.be)/i.test(trimmedFileName);
        
        if (!isUrl) {
          const mediaItem = mediaBinItemsRef.current.find(item => item.name.trim() === trimmedFileName);
          
          if (mediaItem) {
            fileUrl = mediaItem.mediaUrlRemote || mediaItem.gcsUri || '';
            
            if (!fileUrl) {
              throw new Error(`Media item "${trimmedFileName}" has no URL available`);
            }
          } else {
            throw new Error(`Media item "${trimmedFileName}" not found in library`);
          }
        }
        
        return {
          file_url: fileUrl,
          title: trimmedFileName,
          question: video.question
        };
      })
    );
    
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(apiUrl('/api/v1/analysis/media/batch'), {
        method: 'POST',
        headers,
        body: JSON.stringify({
          videos: resolvedVideos,
          max_concurrent: 4,
          audio_timestamp: true
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
      
      const responseMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: aggregatedAnalysis,
        isUser: false,
        timestamp: new Date(),
        isAnalysisResult: true,
        sender: 'tool'
      };

      // Immediately add to collapsed state
      setCollapsedMessages(prev => {
        const newSet = new Set(prev);
        newSet.add(responseMessage.id);
        return newSet;
      });
      
      return [responseMessage];

    } catch (error) {
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
  }, [getAuthHeaders, mediaBinItemsRef, setCollapsedMessages]);

  // Generate image/video/audio content
  const generateMedia = useCallback(async (
    prompt: string,
    suggestedName: string,
    description: string,
    contentType: 'image' | 'video' | 'logo' | 'audio' = 'image',
    seedImageFileName?: string,
    voiceSettings?: { voice_id?: string; language_code?: string; speaking_rate?: number; pitch?: number },
    signal?: AbortSignal
  ): Promise<{ messages: Message[]; newMediaItem: MediaBinItem | null }> => {
    try {
      const requestBody: Record<string, unknown> = {
        content_type: contentType,
        prompt: prompt,
      };

      if (contentType === 'video') {
        requestBody.aspect_ratio = "16:9";
        requestBody.resolution = "720p";
        
        if (seedImageFileName) {
          const seedImage = mediaBinItems.find((item: MediaBinItem) => item.name === seedImageFileName);
          if (seedImage) {
            const imageUrl = seedImage.mediaUrlRemote || seedImage.mediaUrlLocal;
            if (imageUrl) {
              requestBody.reference_image_url = imageUrl;
            }
          }
        }
      }

      if (contentType === 'audio' && voiceSettings) {
        requestBody.voice_settings = voiceSettings;
      }

      const headers = await getAuthHeaders();
      const response = await fetch(apiUrl('/api/v1/media/generate'), {
        method: 'POST',
        headers,
        body: JSON.stringify(requestBody),
        signal
      });

      if (!response.ok) {
        throw new Error(`Generation failed: ${response.status} ${response.statusText}`);
      }

      const result = await response.json();

      if (!result.success) {
        throw new Error(result.error_message || 'Generation failed');
      }

      let generatedAsset;
      
      if (result.status === 'processing' && result.operation_id) {
        const maxAttempts = 120;
        let attempts = 0;
        let delay = 5000;
        
        while (attempts < maxAttempts) {
          await new Promise(resolve => setTimeout(resolve, delay));
          
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
          
          if (statusResult.status === 'completed') {
            generatedAsset = statusResult.generated_asset;
            break;
          } else if (statusResult.status === 'failed') {
            throw new Error(statusResult.error_message || 'Video generation failed');
          }
          
          attempts++;
          delay = Math.min(delay * 1.2, 30000);
        }
        
        if (!generatedAsset) {
          throw new Error('Video generation timed out after 10 minutes');
        }
      } else {
        generatedAsset = result.generated_asset;
      }

      const fastApiBaseUrl = getApiBaseUrl(true);
      const mediaUrl = generatedAsset.file_url.startsWith('http') 
        ? generatedAsset.file_url 
        : `${fastApiBaseUrl}${generatedAsset.file_url}`;

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

      if (onAddGeneratedImage) {
        await onAddGeneratedImage(newMediaItem);
        mediaBinItemsRef.current = [...mediaBinItemsRef.current, newMediaItem];
      }

      const generationContent = `Successfully generated ${contentType}: ${name}. The ${contentType} has been added to your media library.`;
      
      const generationMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: generationContent,
        isUser: false,
        sender: 'tool',
        timestamp: new Date(),
        isSystemMessage: true,
        word_timestamps: contentType === 'audio' && generatedAsset.word_timestamps ? generatedAsset.word_timestamps : undefined,
      };
      
      const messages: Message[] = [generationMessage];
      if (contentType === 'audio' && generatedAsset.word_timestamps && generatedAsset.word_timestamps.length > 0) {
        const timestampsJson = JSON.stringify(generatedAsset.word_timestamps, null, 2);
        const agentTimestampMessage: Message = {
          id: (Date.now() + 2).toString(),
          content: `Sentence timestamps: ${timestampsJson}`,
          isUser: false,
          sender: 'tool',
          timestamp: new Date(),
          isSystemMessage: true,
          alreadyInUI: true,
        };
        messages.push(agentTimestampMessage);
      }

      return { messages, newMediaItem };

    } catch (error) {
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
  }, [getAuthHeaders, mediaBinItems, mediaBinItemsRef, onAddGeneratedImage]);

  // Fetch stock videos from Pexels
  const fetchStockVideos = useCallback(async (
    provider: 'pexels' | 'shutterstock',
    query: string,
    count: number,
    signal?: AbortSignal
  ): Promise<Message[]> => {
    try {
      const fetchUrl = apiUrl("/api/v1/stock/search");
      
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

      if (!result.success || !result.items || result.items.length === 0) {
        throw new Error(result.error_message || "No videos found");
      }

      const videoOptions = result.items.map((item: Record<string, unknown>, index: number) => ({
        id: item.id,
        title: `Option ${index + 1}`,
        duration: item.duration ? `${item.duration}s` : 'N/A',
        description: `${(item.quality as string)?.toUpperCase() || 'HD'} quality - ${item.width}x${item.height} - by ${item.creator_name}`,
        thumbnailUrl: item.preview_url,
        downloadUrl: item.storage_url,
        pexelsUrl: item.provider_url,
        width: item.width,
        height: item.height,
        durationInSeconds: item.duration
      }));

      if (onAddGeneratedImage) {
        for (const item of result.items) {
          const videoUrl = item.storage_url as string;
          const name = item.name as string;

          const mediaItem: MediaBinItem = {
            id: generateUUID(),
            name,
            title: name,
            mediaType: "video",
            mediaUrlLocal: null,
            mediaUrlRemote: videoUrl,
            media_width: item.width as number,
            media_height: item.height as number,
            durationInSeconds: item.duration as number,
            text: null,
            isUploading: false,
            uploadProgress: null,
            upload_status: 'uploaded',
            gemini_file_id: null,
            left_transition_id: null,
            right_transition_id: null,
          };
          
          await onAddGeneratedImage(mediaItem);
          mediaBinItemsRef.current = [...mediaBinItemsRef.current, mediaItem];
        }
      }

      const addedNames = result.items.map((item: Record<string, unknown>) => item.name).filter(Boolean);
      const addedNamesText = addedNames.length > 0
        ? ` as: ${addedNames.join(', ')}`
        : '';
      const videoOptionsMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `I found ${result.items.length} stock videos for "${query}". All videos have been added to your media library${addedNamesText}. Click to preview:`,
        isUser: false,
        sender: 'tool',
        timestamp: new Date(),
        isSystemMessage: false,
        isVideoSelection: true,
        videoOptions: videoOptions,
      };

      return [videoOptionsMessage];

    } catch (error) {
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
  }, [getAuthHeaders, mediaBinItemsRef, onAddGeneratedImage]);

  return {
    probeMedia,
    generateMedia,
    fetchStockVideos,
  };
}
