/**
 * @deprecated This hook is deprecated. Files are now uploaded directly to GCS via /api/v1/upload/upload
 * Gemini can access GCS URLs directly when needed for analysis.
 * This file is kept for backwards compatibility but should not be used in new code.
 */

import { useState, useCallback } from 'react';
import { apiUrl } from '~/utils/api';

export interface GeminiUploadProgress {
  status: 'idle' | 'uploading' | 'uploaded' | 'error';
  progress: number; // 0-100
  gemini_file_id: string | null;
  error?: string;
}

export interface UseGeminiUploadOptions {
  onStatusChange?: (videoId: string, status: GeminiUploadProgress) => void;
}

export const useGeminiUpload = (options?: UseGeminiUploadOptions) => {
  const [uploads, setUploads] = useState<Map<string, GeminiUploadProgress>>(new Map());

  const updateUploadStatus = useCallback((videoId: string, status: GeminiUploadProgress) => {
    console.log(`🔄 [STATUS UPDATE] videoId: ${videoId}, status: ${status.status}, progress: ${status.progress}`);
    setUploads(prev => {
      const newMap = new Map(prev);
      newMap.set(videoId, status);
      return newMap;
    });
    
    // Notify parent component
    console.log(`🔔 [CALLBACK] Calling onStatusChange for videoId: ${videoId}`);
    options?.onStatusChange?.(videoId, status);
  }, [options]);

  const uploadVideoToGemini = useCallback(async (
    videoUrl: string, 
    videoId: string,
    filename: string
  ): Promise<string | null> => {
    console.log(`📤 [UPLOAD START] videoId: ${videoId}, filename: ${filename}, url: ${videoUrl}`);
    
    updateUploadStatus(videoId, {
      status: 'uploading',
      progress: 0,
      gemini_file_id: null
    });

    try {
      // Download the video file first
      console.log(`📥 [DOWNLOAD START] Downloading from: ${videoUrl}`);
      const response = await fetch(videoUrl);
      if (!response.ok) {
        throw new Error(`Failed to download video: ${response.status}`);
      }

      const blob = await response.blob();
      console.log(`📥 [DOWNLOAD SUCCESS] Downloaded ${blob.size} bytes, type: ${blob.type}`);
      const file = new File([blob], filename, { type: blob.type });

      // Upload to Gemini Files API
      const formData = new FormData();
      formData.append('file', file);

      updateUploadStatus(videoId, {
        status: 'uploading',
        progress: 50,
        gemini_file_id: null
      });

      console.log(`📤 [UPLOAD TO GEMINI] Starting upload for videoId: ${videoId}`);
      const geminiResponse = await fetch(apiUrl('/upload-to-gemini', true), {
        method: 'POST',
        body: formData,
      });

      if (!geminiResponse.ok) {
        const errorText = await geminiResponse.text();
        console.error(`❌ [UPLOAD FAILED] Status: ${geminiResponse.status}, Response: ${errorText}`);
        throw new Error(`Gemini upload failed: ${geminiResponse.status}`);
      }

      const result = await geminiResponse.json();
      console.log(`📤 [UPLOAD RESPONSE] videoId: ${videoId}, result:`, result);
      
      if (!result.success) {
        throw new Error(result.error_message || 'Gemini upload failed');
      }

      const geminiFileId = result.gemini_file_id;
      console.log(`✅ [UPLOAD SUCCESS] videoId: ${videoId}, geminiFileId: ${geminiFileId}`);

      updateUploadStatus(videoId, {
        status: 'uploaded',
        progress: 100,
        gemini_file_id: geminiFileId
      });

      return geminiFileId;

    } catch (error) {
      console.error(`❌ Gemini upload failed for ${videoId}:`, error);
      
      updateUploadStatus(videoId, {
        status: 'error',
        progress: 0,
        gemini_file_id: null,
        error: error instanceof Error ? error.message : 'Unknown error'
      });

      return null;
    }
  }, [updateUploadStatus]);

  const getUploadStatus = useCallback((videoId: string): GeminiUploadProgress | null => {
    return uploads.get(videoId) || null;
  }, [uploads]);

  const clearUploadStatus = useCallback((videoId: string) => {
    setUploads(prev => {
      const newMap = new Map(prev);
      newMap.delete(videoId);
      return newMap;
    });
  }, []);

  return {
    uploadVideoToGemini,
    getUploadStatus,
    clearUploadStatus,
    uploads: Array.from(uploads.entries()).map(([id, status]) => ({ id, ...status }))
  };
};
