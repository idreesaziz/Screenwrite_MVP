import { useState, useCallback } from "react"
import axios from "axios"
import { type MediaBinItem } from "~/components/editor/timeline/types"
import { generateUUID } from "~/lib/uuid"
import { apiUrl } from "~/lib/api"
import { uploadFileToGCS, type GetTokenFn } from "~/lib/authApi"


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

    try {
      const mediaUrlLocal = URL.createObjectURL(file);

      const metadata = await getMediaMetadata(file, mediaType);

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

      // Upload to GCS with JWT authentication
      const uploadResult = await uploadFileToGCS(
        file,
        getToken,
        (percentCompleted: number) => {
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
    setMediaBinItems(prev => [...prev, item]);
  }, []);

  const handleDeleteMedia = useCallback(async (item: MediaBinItem) => {
    // Remove from media bin state
    setMediaBinItems(prev => prev.filter(binItem => binItem.id !== item.id));
    
    // Also remove any scrubbers from the timeline that use this media
    if (handleDeleteScrubbersByMediaBinId) {
      handleDeleteScrubbersByMediaBinId(item.id);
    }
  }, [handleDeleteScrubbersByMediaBinId]);

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

  // Allow setting the entire media bin (for session restore)
  const handleSetMediaBin = useCallback((items: MediaBinItem[]) => {
    setMediaBinItems(items);
  }, []);

  return {
    mediaBinItems,
    handleAddMediaToBin,
    handleAddTextToBin,
    handleAddDirectMediaBinItem,
    handleUpdateMediaItem,
    handleDeleteMedia,
    handleSetMediaBin,
    contextMenu,
    handleContextMenu,
    handleDeleteFromContext,
    handleCloseContextMenu,
  }
} 