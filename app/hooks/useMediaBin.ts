import { useState, useCallback } from "react"
import axios from "axios"
import { type MediaBinItem } from "~/components/timeline/types"
import { generateUUID } from "~/utils/uuid"
import { apiUrl } from "~/utils/api"
import { uploadFileToGCS, type GetTokenFn } from "~/utils/authApi"

// Delete media file from server (Node.js render server, port 8000)
export const deleteMediaFile = async (filename: string): Promise<{ success: boolean; message?: string; error?: string }> => {
  try {
    const response = await fetch(apiUrl(`/media/${encodeURIComponent(filename)}`, false), {
      method: 'DELETE',
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to delete file');
    }

    return await response.json();
  } catch (error) {
    console.error('Delete API error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred'
    };
  }
};

// Clone/copy media file on server (Node.js render server, port 8000)
export const cloneMediaFile = async (filename: string, originalName: string, suffix: string): Promise<{ success: boolean; filename?: string; originalName?: string; url?: string; fullUrl?: string; size?: number; error?: string }> => {
  try {
    const response = await fetch(apiUrl('/clone-media', false), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        filename,
        originalName,
        suffix
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to clone file');
    }

    return await response.json();
  } catch (error) {
    console.error('Clone API error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred'
    };
  }
};


// Helper function to get media metadata
const getMediaMetadata = (file: File, mediaType: "video" | "image" | "audio"): Promise<{
  durationInSeconds?: number;
  width: number;
  height: number;
}> => {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);

    if (mediaType === "video") {
      const video = document.createElement("video");
      video.preload = "metadata";

      video.onloadedmetadata = () => {
        const width = video.videoWidth;
        const height = video.videoHeight;
        const durationInSeconds = video.duration;

        URL.revokeObjectURL(url);
        resolve({
          durationInSeconds: isFinite(durationInSeconds) ? durationInSeconds : undefined,
          width,
          height
        });
      };

      video.onerror = () => {
        URL.revokeObjectURL(url);
        reject(new Error("Failed to load video metadata"));
      };

      video.src = url;
    } else if (mediaType === "image") {
      const img = new Image();

      img.onload = () => {
        const width = img.naturalWidth;
        const height = img.naturalHeight;

        URL.revokeObjectURL(url);
        resolve({
          durationInSeconds: undefined, // Images don't have duration
          width,
          height
        });
      };

      img.onerror = () => {
        URL.revokeObjectURL(url);
        reject(new Error("Failed to load image metadata"));
      };

      img.src = url;
    } else if (mediaType === "audio") {
      const audio = document.createElement("audio");
      audio.preload = "metadata";

      audio.onloadedmetadata = () => {
        const durationInSeconds = audio.duration;

        URL.revokeObjectURL(url);
        resolve({
          durationInSeconds: isFinite(durationInSeconds) ? durationInSeconds : undefined,
          width: 0, // Audio files don't have visual dimensions
          height: 0
        });
      };

      audio.onerror = () => {
        URL.revokeObjectURL(url);
        reject(new Error("Failed to load audio metadata"));
      };

      audio.src = url;
    }
  });
};

export const useMediaBin = (
  handleDeleteScrubbersByMediaBinId: (mediaBinId: string) => void,
  getToken: GetTokenFn
) => {
  const [mediaBinItems, setMediaBinItems] = useState<MediaBinItem[]>([])
  const [contextMenu, setContextMenu] = useState<{
    x: number;
    y: number;
    item: MediaBinItem;
  } | null>(null)

  const handleAddMediaToBin = useCallback(async (file: File) => {
    const id = generateUUID();
    
    let mediaType: "video" | "image" | "audio";
    if (file.type.startsWith("video/")) mediaType = "video";
    else if (file.type.startsWith("image/")) mediaType = "image";
    else if (file.type.startsWith("audio/")) mediaType = "audio";
    else {
      alert("Unsupported file type. Please select a video or image.");
      return;
    }

    console.log("Adding to bin:", { filename: file.name, mediaType });

    try {
      const mediaUrlLocal = URL.createObjectURL(file);

      console.log(`Parsing ${mediaType} file for metadata...`);
      const metadata = await getMediaMetadata(file, mediaType);
      console.log("Media metadata:", metadata);

      // Add item to media bin immediately with upload progress tracking
      // Name will be provided by backend after upload
      const newItem: MediaBinItem = {
        id,
        name: "uploading...", // Temporary name until backend returns unique name
        mediaType,
        mediaUrlLocal,
        mediaUrlRemote: null,
        durationInSeconds: metadata.durationInSeconds ?? 0,
        media_width: metadata.width,
        media_height: metadata.height,
        text: null,
        isUploading: true,
        uploadProgress: 0,
        upload_status: 'pending',
        gemini_file_id: null,
        left_transition_id: null,
        right_transition_id: null,
      };
      setMediaBinItems(prev => [...prev, newItem]);

      console.log("Uploading file to GCS...");
      
      // Upload to GCS with JWT authentication
      const uploadResult = await uploadFileToGCS(
        file,
        getToken,
        (percentCompleted) => {
          console.log(`Upload progress: ${percentCompleted}%`);
          
          // Update upload progress in the media bin
          setMediaBinItems(prev =>
            prev.map(item =>
              item.id === id
                ? { ...item, uploadProgress: percentCompleted }
                : item
            )
          );
        }
      );

      console.log("✅ GCS upload successful!");
      console.log("📦 Upload result:", uploadResult);
      console.log("🔗 Signed URL:", uploadResult.signed_url);
      console.log("🔗 GCS URI:", uploadResult.gcs_uri);
      console.log("🏷️  Name from backend:", uploadResult.name);

      // Update item with successful GCS upload result and backend-provided name
      setMediaBinItems(prev =>
        prev.map(item =>
          item.id === id
            ? {
              ...item,
              name: uploadResult.name, // Use name from backend
              mediaUrlRemote: uploadResult.signed_url || uploadResult.file_url,
              gcsUri: uploadResult.gcs_uri,
              isUploading: false,
              uploadProgress: null,
            }
            : item
        )
      );

      console.log("✅ Media item updated with name:", uploadResult.name);

    } catch (error) {
      console.error("Error adding media to bin:", error);
      
      // Provide user-friendly error messages
      let errorMessage: string;
      if (error instanceof Error) {
        if (error.message.includes("No authentication token")) {
          errorMessage = "Authentication required. Please sign in to upload media.";
        } else if (error.message.includes("Network Error") || error.message.includes("ERR_NETWORK")) {
          errorMessage = "Network connection error. Please check your internet connection and try again.";
        } else if (error.message.includes("timeout")) {
          errorMessage = "Upload timeout. Please try again with a smaller file or check your connection.";
        } else if (error.message.includes("401") || error.message.includes("403")) {
          errorMessage = "Authentication error. Please sign in again.";
        } else {
          errorMessage = `Upload failed: ${error.message}`;
        }
      } else {
        errorMessage = "Upload failed due to an unknown error. Please try again.";
      }

      // Remove the failed item from media bin
      setMediaBinItems(prev => prev.filter(item => item.id !== id));

      throw new Error(errorMessage);
    }
  }, [getToken]);

  const handleAddTextToBin = useCallback((
    textContent: string,
    fontSize: number = 48,
    fontFamily: string = "Arial",
    color: string = "#ffffff",
    textAlign: "left" | "center" | "right" = "center",
    fontWeight: "normal" | "bold" = "normal"
  ) => {
    // Use first 50 chars of text as base name
    const baseTitle = textContent.trim().substring(0, 50) || "text";
    
    // Simple uniqueness check with counter
    const existingNames = new Set(mediaBinItems.map(item => item.name));
    let name = baseTitle;
    let counter = 2;
    while (existingNames.has(name)) {
      name = `${baseTitle}_${counter}`;
      counter++;
    }
    
    const newItem: MediaBinItem = {
      id: generateUUID(),
      name,
      mediaType: "text",
      media_width: 0,
      media_height: 0,
      text: {
        textContent,
        fontSize,
        fontFamily,
        color,
        textAlign,
        fontWeight,
      },
      mediaUrlLocal: null,
      mediaUrlRemote: null,
      durationInSeconds: 0,
      isUploading: false,
      uploadProgress: null,
      upload_status: 'not_uploaded',
      gemini_file_id: null,
      left_transition_id: null,
      right_transition_id: null,
    };
    setMediaBinItems(prev => [...prev, newItem]);
  }, [mediaBinItems]);

  // Function to directly add a pre-created MediaBinItem (for generated content)
  const handleAddDirectMediaBinItem = useCallback((item: MediaBinItem) => {
    console.log("📦 Adding direct MediaBinItem to bin:", item);
    setMediaBinItems(prev => [...prev, item]);
  }, []);

  const handleDeleteMedia = useCallback(async (item: MediaBinItem) => {
    try {
      if (item.mediaType === "text") {
        setMediaBinItems(prev => prev.filter(binItem => binItem.id !== item.id));

        // Also remove any scrubbers from the timeline that use this media
        if (handleDeleteScrubbersByMediaBinId) {
          handleDeleteScrubbersByMediaBinId(item.id);
        }
        return;
      }

      // Extract filename from mediaUrlRemote URL
      if (!item.mediaUrlRemote) {
        console.error('No remote URL found for media item');
        return;
      }

      // Parse the URL and extract filename from the path
      const url = new URL(item.mediaUrlRemote);
      const pathSegments = url.pathname.split('/');
      const encodedFilename = pathSegments[pathSegments.length - 1]; // Get the last segment after /media/

      if (!encodedFilename) {
        console.error('Could not extract filename from URL:', item.mediaUrlRemote);
        return;
      }

      // Decode the filename
      const filename = decodeURIComponent(encodedFilename);
      console.log('Extracted filename:', filename);

      const result = await deleteMediaFile(filename);
      if (result.success) {
        console.log(`Media deleted: ${item.name}`);
        // Remove from media bin state
        setMediaBinItems(prev => prev.filter(binItem => binItem.id !== item.id));
        // Also remove any scrubbers from the timeline that use this media
        if (handleDeleteScrubbersByMediaBinId) {
          handleDeleteScrubbersByMediaBinId(item.id);
        }
      } else {
        console.error('Failed to delete media:', result.error);
      }
    } catch (error) {
      console.error('Error deleting media:', error);
    }
  }, [handleDeleteScrubbersByMediaBinId]);

  const handleSplitAudio = useCallback(async (videoItem: MediaBinItem) => {
    if (videoItem.mediaType !== 'video') {
      throw new Error('Can only split audio from video files');
    }

    try {
      // Extract filename from mediaUrlRemote URL
      if (!videoItem.mediaUrlRemote) {
        throw new Error('No remote URL found for video item');
      }

      // Parse the URL and extract filename from the path
      const url = new URL(videoItem.mediaUrlRemote);
      const pathSegments = url.pathname.split('/');
      const encodedFilename = pathSegments[pathSegments.length - 1];

      if (!encodedFilename) {
        throw new Error('Could not extract filename from URL');
      }

      // Clone the file on the server
      const cloneResult = await cloneMediaFile(encodedFilename, videoItem.name, '(Audio)');

      if (!cloneResult.success) {
        throw new Error(cloneResult.error || 'Failed to clone media file');
      }

      // Create a new audio media item with the cloned file info
      const audioItem: MediaBinItem = {
        id: generateUUID(),
        name: `${videoItem.name} (Audio)`,
        mediaType: "audio",
        mediaUrlLocal: videoItem.mediaUrlLocal, // Reuse the original video's blob URL
        mediaUrlRemote: cloneResult.fullUrl!, // Use the new cloned file URL
        durationInSeconds: videoItem.durationInSeconds,
        media_width: 0, // Audio doesn't have visual dimensions
        media_height: 0,
        text: null,
        isUploading: false,
        uploadProgress: null,
        left_transition_id: null,
        right_transition_id: null,
      };

      // Add the audio item to the media bin
      setMediaBinItems(prev => [...prev, audioItem]);
      setContextMenu(null); // Close context menu after action

      console.log(`Audio split successful: ${videoItem.name} -> ${audioItem.name}`);
    } catch (error) {
      console.error('Error splitting audio:', error);
      throw error;
    }
  }, []);

  // Handle right-click to show context menu
  const handleContextMenu = useCallback((e: React.MouseEvent, item: MediaBinItem) => {
    e.preventDefault();
    setContextMenu({
      x: e.clientX,
      y: e.clientY,
      item,
    });
  }, []);

  // Handle context menu actions
  const handleDeleteFromContext = useCallback(async () => {
    if (!contextMenu) return;
    await handleDeleteMedia(contextMenu.item);
    setContextMenu(null);
  }, [contextMenu, handleDeleteMedia]);

  const handleSplitAudioFromContext = useCallback(async () => {
    if (!contextMenu) return;
    await handleSplitAudio(contextMenu.item);
  }, [contextMenu, handleSplitAudio]);

  // Close context menu when clicking outside
  const handleUpdateMediaItem = useCallback((updatedItem: MediaBinItem) => {
    setMediaBinItems(prev => 
      prev.map(item => 
        item.id === updatedItem.id ? updatedItem : item
      )
    );
  }, []);

  const handleCloseContextMenu = useCallback(() => {
    setContextMenu(null);
  }, []);

  return {
    mediaBinItems,
    handleAddMediaToBin,
    handleAddTextToBin,
    handleAddDirectMediaBinItem,
    handleUpdateMediaItem,
    handleDeleteMedia,
    handleSplitAudio,
    contextMenu,
    handleContextMenu,
    handleDeleteFromContext,
    handleSplitAudioFromContext,
    handleCloseContextMenu,
  }
} 