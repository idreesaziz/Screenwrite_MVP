/**
 * API Configuration
 * Handles environment-aware URL routing for backend services
 */

// Environment detection
const isDevelopment = import.meta.env.DEV;
const isProduction = import.meta.env.PROD;

// Backend URLs from environment variables (set at build time)
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "";

/**
 * Get the base URL for the FastAPI backend
 * Development: http://127.0.0.1:8001
 * Production: Uses VITE_BACKEND_URL environment variable
 */
export const getBackendUrl = (): string => {
  if (isDevelopment) {
    return "http://127.0.0.1:8001";
  }

  if (isProduction && BACKEND_URL) {
    return BACKEND_URL;
  }

  // Fallback: assume reverse proxy at /api
  return typeof window !== "undefined" ? `${window.location.origin}/api` : "/api";
};

/**
 * Construct a full API URL for a given endpoint
 * @param endpoint - API endpoint path (e.g., "/api/v1/sessions")
 * @returns Full URL including base
 */
export const apiUrl = (endpoint: string): string => {
  const baseUrl = getBackendUrl();
  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  return `${baseUrl}${cleanEndpoint}`;
};

// Legacy compatibility: getApiBaseUrl alias
export const getApiBaseUrl = getBackendUrl;

// New interface for AI composition generation
export interface ConversationMessage {
  user_request: string;
  ai_response: string;
  generated_code: string;
  timestamp: string;
}

export interface CompositionRequest {
  user_request: string;
  current_content: any[];
  preview_settings: any;
  media_library?: any[]; // Optional list of available media files
  current_generated_code?: string; // Optional current AI-generated TSX code for context
  conversation_history?: ConversationMessage[]; // Past requests and responses for context
  provider?: string; // AI provider ("gemini" or "claude")
}

export interface CompositionResponse {
  composition_code: string;
  content_data: any[];
  explanation: string;
  duration: number;
  success: boolean;
  error_message?: string;
}

// Function to generate composition via AI
export async function generateComposition(request: CompositionRequest): Promise<CompositionResponse> {
  try {
    const response = await fetch(apiUrl("/api/v1/compositions/generate"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error generating composition:", error);
    return {
      composition_code: "",
      content_data: [],
      explanation: "Failed to generate composition",
      duration: 0,
      success: false,
      error_message: error instanceof Error ? error.message : "Unknown error",
    };
  }
}