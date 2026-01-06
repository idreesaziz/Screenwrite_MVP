/**
 * Hook for managing chat sessions.
 * Handles session CRUD, auto-save, and state synchronization.
 */

import { useState, useCallback, useRef, useEffect } from "react";
import {
  createSession,
  listSessions,
  getSession,
  saveSessionState,
  deleteSession,
  toFrontendMessage,
  toFrontendMediaBinItem,
  type Session,
  type SessionListItem,
  type ChatMessage,
  type MissingFile,
} from "~/lib/sessionApi";
import type { CompositionBlueprint } from "~/composition/BlueprintTypes";
import type { MediaBinItem } from "~/lib/media";

interface UseSessionOptions {
  getToken: () => Promise<string | null>;
  autoSaveDebounceMs?: number;
}

interface LoadSessionResult {
  messages: ChatMessage[];
  composition: CompositionBlueprint | null;
  mediaBin: MediaBinItem[];
  missingFiles: MissingFile[];
}

interface UseSessionReturn {
  // Current session
  currentSessionId: string | null;
  sessions: SessionListItem[];
  isLoading: boolean;
  error: string | null;
  
  // Session operations
  startNewSession: () => void;
  loadSession: (sessionId: string) => Promise<LoadSessionResult | null>;
  saveCurrentSession: (
    messages: ChatMessage[],
    composition: CompositionBlueprint | null,
    mediaBin?: MediaBinItem[]
  ) => Promise<void>;
  removeSession: (sessionId: string) => Promise<void>;
  refreshSessions: () => Promise<void>;
  
  // Session creation (called on first message)
  ensureSession: (
    firstMessage: string,
    composition?: CompositionBlueprint | null,
    mediaBin?: MediaBinItem[]
  ) => Promise<string>;
}

export function useSession({
  getToken,
  autoSaveDebounceMs = 3000,
}: UseSessionOptions): UseSessionReturn {
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [sessions, setSessions] = useState<SessionListItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Debounce timer ref for auto-save
  const saveTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  
  // Track pending save to prevent data loss
  const pendingSaveRef = useRef<{
    messages: ChatMessage[];
    composition: CompositionBlueprint | null;
    mediaBin?: MediaBinItem[];
  } | null>(null);

  /**
   * Load the list of sessions.
   */
  const refreshSessions = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const result = await listSessions(getToken, 50, 0);
      setSessions(result.sessions);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load sessions";
      setError(message);
      console.error("Failed to refresh sessions:", err);
    } finally {
      setIsLoading(false);
    }
  }, [getToken]);

  /**
   * Start a new session (clears current session, actual creation happens on first message).
   */
  const startNewSession = useCallback(() => {
    // Flush any pending save before switching
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
      saveTimeoutRef.current = null;
    }
    
    setCurrentSessionId(null);
    setError(null);
  }, []);

  /**
   * Ensure a session exists, creating one if needed.
   * Called when sending the first message.
   */
  const ensureSession = useCallback(async (
    firstMessage: string,
    composition?: CompositionBlueprint | null,
    mediaBin?: MediaBinItem[]
  ): Promise<string> => {
    if (currentSessionId) {
      return currentSessionId;
    }
    
    try {
      setIsLoading(true);
      setError(null);
      
      const session = await createSession(firstMessage, getToken, composition, mediaBin);
      setCurrentSessionId(session.id);
      
      // Refresh the session list to include the new session
      await refreshSessions();
      
      return session.id;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to create session";
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [currentSessionId, getToken, refreshSessions]);

  /**
   * Load a session and return its data.
   */
  const loadSession = useCallback(async (sessionId: string): Promise<LoadSessionResult | null> => {
    // Flush any pending save before switching
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
      saveTimeoutRef.current = null;
    }
    
    if (pendingSaveRef.current && currentSessionId) {
      // Save pending changes to the old session before loading new one
      try {
        await saveSessionState(
          currentSessionId,
          pendingSaveRef.current.messages,
          pendingSaveRef.current.composition,
          getToken,
          pendingSaveRef.current.mediaBin
        );
      } catch (err) {
        console.error("Failed to save pending changes:", err);
      }
      pendingSaveRef.current = null;
    }
    
    try {
      setIsLoading(true);
      setError(null);
      
      const session = await getSession(sessionId, getToken);
      setCurrentSessionId(session.id);
      
      // Convert backend messages to frontend format
      const frontendMessages = (session.messages || []).map((msg, index) => 
        toFrontendMessage(msg, index)
      );
      
      // Convert backend media bin items to frontend format
      const frontendMediaBin = (session.media_bin || []).map(item => 
        toFrontendMediaBinItem(item)
      );
      
      return {
        messages: frontendMessages,
        composition: session.composition,
        mediaBin: frontendMediaBin,
        missingFiles: session.missing_files || [],
      };
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load session";
      setError(message);
      console.error("Failed to load session:", err);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [currentSessionId, getToken]);

  /**
   * Save the current session state (debounced).
   */
  const saveCurrentSession = useCallback(async (
    messages: ChatMessage[],
    composition: CompositionBlueprint | null,
    mediaBin?: MediaBinItem[]
  ): Promise<void> => {
    if (!currentSessionId) {
      // No session yet, store pending data
      pendingSaveRef.current = { messages, composition, mediaBin };
      return;
    }
    
    // Store pending data
    pendingSaveRef.current = { messages, composition, mediaBin };
    
    // Clear existing timeout
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }
    
    // Debounced save
    saveTimeoutRef.current = setTimeout(async () => {
      if (!pendingSaveRef.current || !currentSessionId) return;
      
      try {
        await saveSessionState(
          currentSessionId,
          pendingSaveRef.current.messages,
          pendingSaveRef.current.composition,
          getToken,
          pendingSaveRef.current.mediaBin
        );
        pendingSaveRef.current = null;
      } catch (err) {
        console.error("Failed to save session:", err);
        setError("Failed to save session");
      }
    }, autoSaveDebounceMs);
  }, [currentSessionId, getToken, autoSaveDebounceMs]);

  /**
   * Delete a session.
   */
  const removeSession = useCallback(async (sessionId: string): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);
      
      await deleteSession(sessionId, getToken);
      
      // If deleting current session, clear it
      if (sessionId === currentSessionId) {
        setCurrentSessionId(null);
      }
      
      // Refresh the list
      await refreshSessions();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to delete session";
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [currentSessionId, getToken, refreshSessions]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, []);

  // Load sessions on mount (only once)
  useEffect(() => {
    refreshSessions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return {
    currentSessionId,
    sessions,
    isLoading,
    error,
    startNewSession,
    loadSession,
    saveCurrentSession,
    removeSession,
    refreshSessions,
    ensureSession,
  };
}
