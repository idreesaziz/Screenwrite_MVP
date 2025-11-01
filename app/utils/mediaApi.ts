/**
 * Media generation API utilities for AI-powered image and video generation
 * Supports Google Imagen (images) and Veo (videos) with reference image support
 */

import { apiUrl } from './api';
import type { GetTokenFn } from './authApi';

// Request types
export interface MediaGenerationRequest {
  content_type: 'image' | 'video';
  prompt: string;
  negative_prompt?: string;
  aspect_ratio?: '1:1' | '16:9' | '9:16';
  resolution?: '720p' | '1080p';
  reference_image_url?: string; // For image-to-video generation
}

// Response types
export interface GeneratedAsset {
  asset_id: string;
  content_type: 'image' | 'video';
  file_path: string;
  file_url: string;
  prompt: string;
  width: number;
  height: number;
  duration_seconds?: number;
  file_size: number;
}

export interface MediaGenerationResponse {
  success: boolean;
  status: 'completed' | 'processing' | 'failed';
  generated_asset?: GeneratedAsset;
  operation_id?: string;
  error_message?: string;
}

export interface VideoStatusResponse {
  success: boolean;
  status: 'completed' | 'processing' | 'failed';
  generated_asset?: GeneratedAsset;
  error_message?: string;
}

/**
 * Generate image or video with AI
 * 
 * Images: Returns completed asset immediately
 * Videos: Returns operation_id to poll for completion
 * 
 * @param request - Generation parameters
 * @param getToken - Function to retrieve JWT token
 * @returns Generation response with asset or operation_id
 */
export async function generateMedia(
  request: MediaGenerationRequest,
  getToken: GetTokenFn
): Promise<MediaGenerationResponse> {
  const token = await getToken();
  
  if (!token) {
    throw new Error('No authentication token available. Please sign in.');
  }

  try {
    const response = await fetch(apiUrl('/api/v1/media/generate', true), {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Media generation failed:', error);
    throw error;
  }
}

/**
 * Check status of video generation operation
 * 
 * Poll this endpoint every 5-10 seconds until status is 'completed' or 'failed'
 * 
 * @param operationId - Operation ID from generateMedia response
 * @param getToken - Function to retrieve JWT token
 * @returns Status response with asset when completed
 */
export async function checkMediaStatus(
  operationId: string,
  getToken: GetTokenFn
): Promise<VideoStatusResponse> {
  const token = await getToken();
  
  if (!token) {
    throw new Error('No authentication token available. Please sign in.');
  }

  try {
    const response = await fetch(
      apiUrl(`/api/v1/media/status/${encodeURIComponent(operationId)}`, true),
      {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Status check failed:', error);
    throw error;
  }
}

/**
 * Poll video generation status until completion
 * 
 * Convenience wrapper that polls automatically with exponential backoff
 * 
 * @param operationId - Operation ID from generateMedia response
 * @param getToken - Function to retrieve JWT token
 * @param onProgress - Optional callback for status updates
 * @param maxAttempts - Maximum polling attempts (default: 120 = ~10 minutes)
 * @returns Final status response with asset
 */
export async function pollVideoStatus(
  operationId: string,
  getToken: GetTokenFn,
  onProgress?: (status: VideoStatusResponse) => void,
  maxAttempts: number = 120
): Promise<VideoStatusResponse> {
  let attempts = 0;
  let delay = 5000; // Start with 5 seconds
  const maxDelay = 30000; // Cap at 30 seconds

  while (attempts < maxAttempts) {
    try {
      const status = await checkMediaStatus(operationId, getToken);
      
      if (onProgress) {
        onProgress(status);
      }

      // Return if completed or failed
      if (status.status === 'completed' || status.status === 'failed') {
        return status;
      }

      // Still processing - wait before next poll
      await new Promise(resolve => setTimeout(resolve, delay));
      
      // Exponential backoff
      delay = Math.min(delay * 1.2, maxDelay);
      attempts++;
      
    } catch (error) {
      console.error(`Polling attempt ${attempts + 1} failed:`, error);
      
      // Retry with backoff
      await new Promise(resolve => setTimeout(resolve, delay));
      delay = Math.min(delay * 1.5, maxDelay);
      attempts++;
    }
  }

  throw new Error('Video generation timed out - maximum polling attempts reached');
}

/**
 * Helper: Generate image with Imagen
 * 
 * @param prompt - Image description
 * @param getToken - Function to retrieve JWT token
 * @param aspectRatio - Image aspect ratio (default: 16:9)
 * @returns Generated image asset
 */
export async function generateImage(
  prompt: string,
  getToken: GetTokenFn,
  aspectRatio: '1:1' | '16:9' | '9:16' = '16:9'
): Promise<GeneratedAsset> {
  const response = await generateMedia(
    {
      content_type: 'image',
      prompt,
      aspect_ratio: aspectRatio,
    },
    getToken
  );

  if (!response.success || !response.generated_asset) {
    throw new Error(response.error_message || 'Image generation failed');
  }

  return response.generated_asset;
}

/**
 * Helper: Generate video with Veo (text-to-video)
 * 
 * Returns operation_id - use pollVideoStatus to wait for completion
 * 
 * @param prompt - Video description
 * @param getToken - Function to retrieve JWT token
 * @param options - Video generation options
 * @returns Operation ID for polling
 */
export async function generateVideo(
  prompt: string,
  getToken: GetTokenFn,
  options?: {
    negative_prompt?: string;
    aspect_ratio?: '16:9' | '9:16';
    resolution?: '720p' | '1080p';
  }
): Promise<string> {
  const response = await generateMedia(
    {
      content_type: 'video',
      prompt,
      negative_prompt: options?.negative_prompt,
      aspect_ratio: options?.aspect_ratio || '16:9',
      resolution: options?.resolution || '720p',
    },
    getToken
  );

  if (!response.success || !response.operation_id) {
    throw new Error(response.error_message || 'Video generation failed to start');
  }

  return response.operation_id;
}

/**
 * Helper: Generate video from reference image (image-to-video)
 * 
 * @param prompt - Video description/motion instruction
 * @param referenceImageUrl - URL of seed image (must be accessible to backend)
 * @param getToken - Function to retrieve JWT token
 * @param options - Video generation options
 * @returns Operation ID for polling
 */
export async function generateVideoFromImage(
  prompt: string,
  referenceImageUrl: string,
  getToken: GetTokenFn,
  options?: {
    negative_prompt?: string;
    aspect_ratio?: '16:9' | '9:16';
    resolution?: '720p' | '1080p';
  }
): Promise<string> {
  const response = await generateMedia(
    {
      content_type: 'video',
      prompt,
      reference_image_url: referenceImageUrl,
      negative_prompt: options?.negative_prompt,
      aspect_ratio: options?.aspect_ratio || '16:9',
      resolution: options?.resolution || '720p',
    },
    getToken
  );

  if (!response.success || !response.operation_id) {
    throw new Error(response.error_message || 'Video generation failed to start');
  }

  return response.operation_id;
}
