/**
 * Authenticated API utilities for making requests to the backend with JWT tokens
 */

import axios from 'axios';
import type { AxiosRequestConfig, AxiosResponse } from 'axios';
import { apiUrl } from './api';

/**
 * Get JWT token from Supabase session
 * This function should be provided by the calling component via useAuth hook
 */
export type GetTokenFn = () => Promise<string | null>;

/**
 * Make an authenticated API request with JWT token
 * @param endpoint - API endpoint (e.g., '/upload-media')
 * @param getToken - Function to retrieve JWT token
 * @param config - Axios request configuration
 * @returns Axios response
 */
export async function authenticatedRequest<T = any>(
  endpoint: string,
  getToken: GetTokenFn,
  config: AxiosRequestConfig = {}
): Promise<AxiosResponse<T>> {
  const token = await getToken();
  
  if (!token) {
    throw new Error('No authentication token available. Please sign in.');
  }

  const headers = {
    ...config.headers,
    'Authorization': `Bearer ${token}`,
  };

  return axios({
    ...config,
    url: apiUrl(endpoint, true), // Use backend URL
    headers,
  });
}

/**
 * Upload a file to GCS with JWT authentication
 * @param file - File to upload
 * @param getToken - Function to retrieve JWT token
 * @param onProgress - Optional progress callback
 * @returns Upload response with GCS URL
 */
export async function uploadFileToGCS(
  file: File,
  getToken: GetTokenFn,
  onProgress?: (percentCompleted: number) => void
): Promise<{
  success: boolean;
  file_url: string;
  gcs_uri: string;
  signed_url?: string;
  file_path: string;
  file_size: number;
  content_type?: string;
}> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await authenticatedRequest('/api/v1/upload/upload', getToken, {
    method: 'POST',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total && onProgress) {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        onProgress(percentCompleted);
      }
    },
  });

  return response.data;
}
