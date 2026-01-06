/**
 * Session API utilities for managing chat sessions.
 */

import { apiUrl } from "./api";
import type { CompositionBlueprint } from "~/composition/BlueprintTypes";
import type { MediaBinItem } from "~/components/editor/timeline/types";

// Backend message format (role-based)
export interface BackendChatMessage {
  role: string;
  content: string;
  timestamp?: string;
}

// Frontend message format (UI-friendly)
export interface ChatMessage {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: string;
  sender?: string;
  isExplanationMode?: boolean;
  isAnalysisResult?: boolean;
  isSystemMessage?: boolean;
}

// Media bin item snapshot for storage (no signed URLs)
export interface MediaBinItemSnapshot {
  id: string;
  name: string;
  mediaType: string;
  gcs_path: string | null;
  media_width: number;
  media_height: number;
  durationInSeconds: number;
  text?: {
    textContent: string;
    fontSize: number;
    fontFamily: string;
    color: string;
    textAlign: string;
    fontWeight: string;
  } | null;
}

// Media bin item response (with refreshed URLs)
export interface MediaBinItemResponse {
  id: string;
  name: string;
  mediaType: string;
  mediaUrlRemote: string | null;
  gcsUri: string | null;
  media_width: number;
  media_height: number;
  durationInSeconds: number;
  text?: {
    textContent: string;
    fontSize: number;
    fontFamily: string;
    color: string;
    textAlign: string;
    fontWeight: string;
  } | null;
  upload_status: string;
}

// Missing file info
export interface MissingFile {
  id: string;
  name: string;
  reason: string;
}

export interface Session {
  id: string;
  user_id: string;
  title: string;
  messages: BackendChatMessage[];
  composition: CompositionBlueprint | null;
  media_bin: MediaBinItemResponse[];
  missing_files: MissingFile[];
  created_at: string;
  updated_at: string;
}

export interface SessionListItem {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

interface CreateSessionRequest {
  first_message: string;
  composition?: CompositionBlueprint | null;
  media_bin?: MediaBinItemSnapshot[] | null;
}

interface UpdateSessionRequest {
  title?: string;
  messages?: BackendChatMessage[];
}

interface SaveStateRequest {
  messages: BackendChatMessage[];
  composition: CompositionBlueprint | null;
  media_bin?: MediaBinItemSnapshot[];
}

// Convert frontend message to backend format
export function toBackendMessage(msg: ChatMessage): BackendChatMessage {
  return {
    role: msg.isUser ? "user" : "assistant",
    content: msg.content,
    timestamp: msg.timestamp,
  };
}

// Convert backend message to frontend format
export function toFrontendMessage(msg: BackendChatMessage, index: number): ChatMessage {
  return {
    id: `msg-${index}`,
    content: msg.content,
    isUser: msg.role === "user",
    timestamp: msg.timestamp || new Date().toISOString(),
  };
}

/**
 * Create a new session.
 */
export async function createSession(
  firstMessage: string,
  getToken: () => Promise<string | null>,
  composition?: CompositionBlueprint | null,
  mediaBin?: MediaBinItem[]
): Promise<Session> {
  const token = await getToken();
  
  // Convert media bin to snapshot format if provided
  const mediaBinSnapshot = mediaBin?.map(item => ({
    id: item.id,
    name: item.name,
    mediaType: item.mediaType,
    gcs_path: extractGcsPath(item),
    media_width: item.media_width || 0,
    media_height: item.media_height || 0,
    durationInSeconds: item.durationInSeconds || 0,
    text: item.text,
  }));
  
  const response = await fetch(apiUrl("/api/v1/sessions"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ 
      first_message: firstMessage,
      composition: composition || null,
      media_bin: mediaBinSnapshot || null,
    } as CreateSessionRequest),
  });

  if (!response.ok) {
    throw new Error(`Failed to create session: ${response.statusText}`);
  }

  return response.json();
}

/**
 * List all sessions for the current user.
 */
export async function listSessions(
  getToken: () => Promise<string | null>,
  limit: number = 50,
  offset: number = 0
): Promise<{ sessions: SessionListItem[]; total: number }> {
  const token = await getToken();
  
  const response = await fetch(
    apiUrl(`/api/v1/sessions?limit=${limit}&offset=${offset}`),
    {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to list sessions: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get a specific session by ID.
 */
export async function getSession(
  sessionId: string,
  getToken: () => Promise<string | null>
): Promise<Session> {
  const token = await getToken();
  
  const response = await fetch(apiUrl(`/api/v1/sessions/${sessionId}`), {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to get session: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Update a session (title or messages).
 */
export async function updateSession(
  sessionId: string,
  updates: UpdateSessionRequest,
  getToken: () => Promise<string | null>
): Promise<Session> {
  const token = await getToken();
  
  const response = await fetch(apiUrl(`/api/v1/sessions/${sessionId}`), {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(updates),
  });

  if (!response.ok) {
    throw new Error(`Failed to update session: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Save session state (messages, composition, and media bin).
 * Converts frontend messages to backend format before sending.
 */
export async function saveSessionState(
  sessionId: string,
  messages: ChatMessage[],
  composition: CompositionBlueprint | null,
  getToken: () => Promise<string | null>,
  mediaBin?: MediaBinItem[]
): Promise<Session> {
  const token = await getToken();
  
  // Convert frontend messages to backend format
  const backendMessages = messages.map(toBackendMessage);
  
  // Convert media bin to snapshot format (strip signed URLs, keep gcs_path)
  const mediaBinSnapshots: MediaBinItemSnapshot[] | undefined = mediaBin?.map(item => ({
    id: item.id,
    name: item.name,
    mediaType: item.mediaType,
    gcs_path: extractGcsPath(item),
    media_width: item.media_width,
    media_height: item.media_height,
    durationInSeconds: item.durationInSeconds,
    text: item.text,
  }));
  
  const response = await fetch(apiUrl(`/api/v1/sessions/${sessionId}/state`), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ 
      messages: backendMessages, 
      composition,
      media_bin: mediaBinSnapshots
    } as SaveStateRequest),
  });

  if (!response.ok) {
    throw new Error(`Failed to save session state: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Extract GCS path from a media bin item.
 * The gcsUri is in format gs://bucket/path, we need just the path.
 */
function extractGcsPath(item: MediaBinItem): string | null {
  if (!item.gcsUri) {
    // Try to extract from mediaUrlRemote if it's a GCS signed URL
    if (item.mediaUrlRemote?.includes('storage.googleapis.com')) {
      // URL format: https://storage.googleapis.com/bucket/path?signature...
      try {
        const url = new URL(item.mediaUrlRemote);
        const pathParts = url.pathname.split('/');
        // Remove empty first element and bucket name
        if (pathParts.length >= 3) {
          return pathParts.slice(2).join('/');
        }
      } catch {
        return null;
      }
    }
    return null;
  }
  
  // Extract path from gs://bucket/path format
  const match = item.gcsUri.match(/^gs:\/\/[^/]+\/(.+)$/);
  return match ? match[1] : null;
}

/**
 * Convert backend media bin response to frontend MediaBinItem format.
 */
export function toFrontendMediaBinItem(item: MediaBinItemResponse): MediaBinItem {
  return {
    id: item.id,
    name: item.name,
    mediaType: item.mediaType as "video" | "image" | "audio" | "text" | "element",
    mediaUrlLocal: null, // Not available on restore
    mediaUrlRemote: item.mediaUrlRemote,
    gcsUri: item.gcsUri || undefined,
    media_width: item.media_width,
    media_height: item.media_height,
    durationInSeconds: item.durationInSeconds,
    uploadProgress: null,
    isUploading: false,
    upload_status: item.upload_status as "uploaded" | "not_uploaded" | "pending",
    gemini_file_id: null,
    text: item.text ? {
      textContent: item.text.textContent,
      fontSize: item.text.fontSize,
      fontFamily: item.text.fontFamily,
      color: item.text.color,
      textAlign: item.text.textAlign as "left" | "center" | "right",
      fontWeight: item.text.fontWeight as "normal" | "bold",
    } : null,
    left_transition_id: null,
    right_transition_id: null,
  };
}

/**
 * Delete a session.
 */
export async function deleteSession(
  sessionId: string,
  getToken: () => Promise<string | null>
): Promise<void> {
  const token = await getToken();
  
  const response = await fetch(apiUrl(`/api/v1/sessions/${sessionId}`), {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to delete session: ${response.statusText}`);
  }
}
