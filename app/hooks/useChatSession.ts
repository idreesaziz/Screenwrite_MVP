import { useState, useCallback, useRef, useEffect } from "react";
import { useSession } from "./useSession";
import type { ChatMessage, SessionListItem } from "~/lib/sessionApi";
import type { CompositionBlueprint } from "~/composition";
import type { MediaBinItem } from "~/components/editor/timeline/types";
import { emptyCompositionBlueprint } from "~/composition";

export interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
  sender?: string;
  isExplanationMode?: boolean;
  isAnalysisResult?: boolean;
  isSystemMessage?: boolean;
}

interface ChatSessionState {
  messages: Message[];
  currentSessionId: string | null;
  sessions: SessionListItem[];
  isSessionLoading: boolean;
  loadingSessionId: string | null;
}

interface ChatSessionActions {
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  loadSession: (sessionId: string) => Promise<{
    composition?: CompositionBlueprint;
    mediaBin?: MediaBinItem[];
  } | null>;
  startNewSession: () => void;
  deleteSession: (sessionId: string) => Promise<void>;
}

function convertToSessionMessages(messages: Message[]): ChatMessage[] {
  return messages.map(msg => ({
    id: msg.id,
    content: msg.content,
    isUser: msg.isUser,
    timestamp: msg.timestamp.toISOString(),
    sender: msg.sender,
    isExplanationMode: msg.isExplanationMode,
    isAnalysisResult: msg.isAnalysisResult,
    isSystemMessage: msg.isSystemMessage,
  }));
}

function convertFromSessionMessages(messages: ChatMessage[]): Message[] {
  return messages.map(msg => ({
    id: msg.id,
    content: msg.content,
    isUser: msg.isUser,
    timestamp: new Date(msg.timestamp),
    sender: msg.sender,
    isExplanationMode: msg.isExplanationMode,
    isAnalysisResult: msg.isAnalysisResult,
    isSystemMessage: msg.isSystemMessage,
  }));
}

export function useChatSession(
  getToken: () => Promise<string | null>,
  composition: CompositionBlueprint,
  mediaBinItems: MediaBinItem[],
  onCompositionRestore: (composition: CompositionBlueprint) => void,
  onMediaBinRestore: (items: MediaBinItem[]) => void
): [ChatSessionState, ChatSessionActions] {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loadingSessionId, setLoadingSessionId] = useState<string | null>(null);

  const {
    currentSessionId,
    sessions,
    isLoading: isSessionLoading,
    startNewSession: baseStartNewSession,
    loadSession: baseLoadSession,
    saveCurrentSession,
    removeSession,
    ensureSession,
  } = useSession({ getToken });

  // Track session creation to prevent duplicates
  const isCreatingSessionRef = useRef(false);
  const lastSavedMessagesCountRef = useRef(0);
  const lastSavedCompositionRef = useRef("");
  const lastSavedMediaBinRef = useRef("");

  // Load session and restore state
  const handleLoadSession = useCallback(async (sessionId: string) => {
    setLoadingSessionId(sessionId);
    try {
      const data = await baseLoadSession(sessionId);
      if (data) {
        setMessages(convertFromSessionMessages(data.messages));

        if (data.composition) {
          onCompositionRestore(data.composition);
        }

        if (data.mediaBin && data.mediaBin.length > 0) {
          onMediaBinRestore(data.mediaBin);
        }

        // Handle missing files notification
        if (data.missingFiles && data.missingFiles.length > 0) {
          const missingNames = data.missingFiles.map((f: { name: string }) => f.name).join(", ");
          const systemMessage: Message = {
            id: `missing-files-${Date.now()}`,
            content: `Some media files from this session are no longer available: ${missingNames}`,
            isUser: false,
            timestamp: new Date(),
            isSystemMessage: true,
          };
          setMessages(prev => [...prev, systemMessage]);
        }

        return {
          composition: data.composition,
          mediaBin: data.mediaBin
        };
      }
      return null;
    } finally {
      setLoadingSessionId(null);
    }
  }, [baseLoadSession, onCompositionRestore, onMediaBinRestore]);

  // Start new session
  const handleNewSession = useCallback(() => {
    baseStartNewSession();
    setMessages([]);
    onCompositionRestore(emptyCompositionBlueprint);
    onMediaBinRestore([]);
  }, [baseStartNewSession, onCompositionRestore, onMediaBinRestore]);

  // Auto-save on message changes
  useEffect(() => {
    if (messages.length === 0) return;

    const firstUserMessage = messages.find(msg => msg.isUser);
    if (!firstUserMessage) return;

    if (currentSessionId && messages.length === lastSavedMessagesCountRef.current) {
      return;
    }

    const handleSessionSave = async () => {
      let sessionId = currentSessionId;

      if (!sessionId && !isCreatingSessionRef.current) {
        isCreatingSessionRef.current = true;
        try {
          sessionId = await ensureSession(firstUserMessage.content, composition, mediaBinItems);
        } catch (err) {
          console.error("Failed to create session:", err);
          isCreatingSessionRef.current = false;
          return;
        }
        isCreatingSessionRef.current = false;
      }

      if (!sessionId) return;

      lastSavedMessagesCountRef.current = messages.length;
      saveCurrentSession(convertToSessionMessages(messages), composition, mediaBinItems);
    };

    handleSessionSave();
  }, [messages.length, currentSessionId, ensureSession, saveCurrentSession, composition, mediaBinItems]);

  // Auto-save on composition/media changes
  useEffect(() => {
    if (!currentSessionId) return;

    const compositionJson = JSON.stringify(composition);
    const mediaBinJson = JSON.stringify(mediaBinItems.map(i => i.id));

    if (
      compositionJson === lastSavedCompositionRef.current &&
      mediaBinJson === lastSavedMediaBinRef.current
    ) {
      return;
    }

    lastSavedCompositionRef.current = compositionJson;
    lastSavedMediaBinRef.current = mediaBinJson;

    saveCurrentSession(convertToSessionMessages(messages), composition, mediaBinItems);
  }, [currentSessionId, composition, mediaBinItems, messages, saveCurrentSession]);

  return [
    {
      messages,
      currentSessionId,
      sessions,
      isSessionLoading,
      loadingSessionId
    },
    {
      setMessages,
      loadSession: handleLoadSession,
      startNewSession: handleNewSession,
      deleteSession: removeSession
    }
  ];
}
