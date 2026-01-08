import { useState, useCallback, useRef } from "react";
import type { MediaBinItem } from "~/components/editor/timeline/types";
import type { Message, ConversationMessage, SynthContext, SynthResponse } from "~/types/chat";
import { apiUrl } from "~/lib/api";
import { generateUUID } from "~/lib/uuid";

export interface UseChatWorkflowOptions {
  getAuthHeaders: () => Promise<Record<string, string>>;
  mediaBinItemsRef: React.MutableRefObject<MediaBinItem[]>;
  currentCompositionRef: React.MutableRefObject<string | undefined>;
  selectedModel: string;
  selectedEditProvider: string;
  onMessagesChange: React.Dispatch<React.SetStateAction<Message[]>>;
  onGenerateComposition?: (
    instruction: string,
    mediaLibrary: MediaBinItem[],
    agentProvider: string,
    editProvider: string,
    signal?: AbortSignal
  ) => Promise<boolean>;
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

export interface UseChatWorkflowReturn {
  isInSynthLoop: boolean;
  runAgentWorkflow: (currentMessages: Message[]) => Promise<void>;
  stopWorkflow: () => void;
}

export function useChatWorkflow({
  getAuthHeaders,
  mediaBinItemsRef,
  currentCompositionRef,
  selectedModel,
  selectedEditProvider,
  onMessagesChange,
  onGenerateComposition,
  probeMedia,
  generateMedia,
  fetchStockVideos,
}: UseChatWorkflowOptions): UseChatWorkflowReturn {
  const [isInSynthLoop, setIsInSynthLoop] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  const continueWorkflowRef = useRef<boolean>(false);

  const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

  const waitForCompositionRefresh = useCallback(
    async (
      previousSnapshot: string | undefined,
      timeoutMs = 5000,
      pollIntervalMs = 200
    ) => {
      const startTime = Date.now();
      while (Date.now() - startTime < timeoutMs) {
        if (currentCompositionRef.current !== previousSnapshot) {
          return true;
        }
        await sleep(pollIntervalMs);
      }
      return false;
    },
    [currentCompositionRef]
  );

  // Call the agent API
  const callAgentAPI = useCallback(async (
    context: SynthContext,
    signal?: AbortSignal
  ): Promise<SynthResponse> => {
    const headers = await getAuthHeaders();
    
    const response = await fetch(apiUrl('/api/v1/agent/chat'), {
      method: 'POST',
      headers,
      body: JSON.stringify({
        messages: context.messages.map(msg => ({
          id: msg.id,
          content: msg.content,
          isUser: msg.isUser,
          sender: msg.sender ?? (msg.isUser ? 'user' : 'assistant'),
          timestamp: msg.timestamp.toISOString()
        })),
        currentComposition: context.currentComposition,
        mediaLibrary: context.mediaLibrary,
        compositionDuration: context.compositionDuration,
        provider: context.provider || "gemini"
      }),
      signal
    });

    if (!response.ok) {
      throw new Error(`Agent API error: ${response.status}`);
    }

    return await response.json();
  }, [getAuthHeaders]);

  // Execute the appropriate action based on response type
  const executeResponseAction = useCallback(async (
    synthResponse: SynthResponse,
    addMessage: (msg: Message) => void,
    signal?: AbortSignal
  ): Promise<boolean> => {
    if (synthResponse.type === 'info') {
      const message: Message = {
        id: generateUUID(),
        content: synthResponse.content,
        isUser: false,
        timestamp: new Date(),
        sender: 'assistant'
      };
      addMessage(message);
      return true;
    }
    
    if (synthResponse.type === 'sleep') {
      const message: Message = {
        id: generateUUID(),
        content: synthResponse.content,
        isUser: false,
        timestamp: new Date(),
        sender: 'assistant'
      };
      addMessage(message);
      return false;
    }

    if (synthResponse.type === 'fetch') {
      const announcement: Message = {
        id: generateUUID(),
        content: `Fetching stock videos: ${synthResponse.query}`,
        isUser: false,
        timestamp: new Date(),
        isSystemMessage: true,
        sender: 'assistant'
      };
      addMessage(announcement);

      const results = await fetchStockVideos('pexels', synthResponse.query!, 3, signal);
      results.forEach(msg => addMessage(msg));
      
      return true;
    }

    if (synthResponse.type === 'generate') {
      const contentTypeText = synthResponse.content_type || 'image';
      const announcement: Message = {
        id: generateUUID(),
        content: `Generating ${contentTypeText}: ${synthResponse.prompt}`,
        isUser: false,
        timestamp: new Date(),
        isSystemMessage: true,
        sender: 'assistant'
      };
      addMessage(announcement);

      const result = await generateMedia(
        synthResponse.prompt!,
        synthResponse.suggestedName!,
        synthResponse.content,
        synthResponse.content_type || 'image',
        synthResponse.seedImageFileName,
        synthResponse.voice_settings,
        signal
      );

      result.messages.forEach(msg => addMessage(msg));
      return true;
    }

    if (synthResponse.type === 'probe') {
      const filesToAnalyze = synthResponse.files || [];
      const fileNames = filesToAnalyze.map(f => f.fileName).join(', ');
      const announcement: Message = {
        id: generateUUID(),
        content: `Analyzing ${filesToAnalyze.length} file(s): ${fileNames}`,
        isUser: false,
        timestamp: new Date(),
        isSystemMessage: true,
        sender: 'assistant'
      };
      addMessage(announcement);

      const results = await probeMedia(filesToAnalyze, signal);
      results.forEach(msg => addMessage(msg));

      return true;
    }

    if (synthResponse.type === 'edit') {
      const announcement: Message = {
        id: generateUUID(),
        content: `Applying edits...`,
        isUser: false,
        timestamp: new Date(),
        isSystemMessage: true,
        sender: 'assistant'
      };
      addMessage(announcement);

      const previousCompositionSnapshot = currentCompositionRef.current;
      
      let success = false;
      if (onGenerateComposition) {
        success = await onGenerateComposition(
          synthResponse.content, 
          mediaBinItemsRef.current, 
          selectedModel,
          selectedEditProvider,
          signal
        );
      }
      
      if (success) {
        await waitForCompositionRefresh(previousCompositionSnapshot);
        
        const newCompositionSnapshot = currentCompositionRef.current;
        
        const diffMessage: Message = {
          id: generateUUID(),
          content: "Composition changes:",
          isUser: false,
          timestamp: new Date(),
          isSystemMessage: true,
          sender: 'tool',
          compositionDiff: {
            before: previousCompositionSnapshot || '[]',
            after: newCompositionSnapshot || '[]'
          }
        };
        addMessage(diffMessage);
      }
      
      const resultMessage: Message = {
        id: generateUUID(),
        content: success ? "Edit implemented successfully!" : "Failed to implement the edit. Please try again.",
        isUser: false,
        timestamp: new Date(),
        isSystemMessage: true,
        sender: 'tool'
      };
      addMessage(resultMessage);
      
      return true;
    }

    // Fallback
    const fallbackMsg: Message = {
      id: generateUUID(),
      content: synthResponse.content,
      isUser: false,
      timestamp: new Date(),
      sender: 'assistant'
    };
    addMessage(fallbackMsg);
    return true;
  }, [
    fetchStockVideos,
    generateMedia,
    probeMedia,
    onGenerateComposition,
    mediaBinItemsRef,
    currentCompositionRef,
    selectedModel,
    selectedEditProvider,
    waitForCompositionRefresh
  ]);

  // Main agent workflow loop
  const runAgentWorkflow = useCallback(async (currentMessages: Message[]): Promise<void> => {
    let conversationHistory: Message[] = [...currentMessages];
    let continueWorkflow = true;
    let iterationCount = 0;
    const MAX_ITERATIONS = 20;
    
    const abortController = new AbortController();
    abortControllerRef.current = abortController;
    continueWorkflowRef.current = true;
    
    setIsInSynthLoop(true);

    const addMessageToHistory = (message: Message) => {
      conversationHistory.push(message);
      onMessagesChange(prev => [...prev, message]);
    };
    
    try {
      while (continueWorkflow && continueWorkflowRef.current && iterationCount < MAX_ITERATIONS) {
        iterationCount++;
      
        try {
          const conversationMessages: ConversationMessage[] = conversationHistory.map(msg => ({
            id: msg.id,
            content: msg.content,
            isUser: msg.isUser,
            timestamp: msg.timestamp,
            sender: msg.sender ?? (msg.isUser ? 'user' : 'assistant')
          }));

          const currentMediaBin = mediaBinItemsRef.current;
          const currentComp = currentCompositionRef.current;
          const synthContext: SynthContext = {
            messages: conversationMessages,
            currentComposition: currentComp ? JSON.parse(currentComp) : undefined,
            mediaLibrary: currentMediaBin,
            compositionDuration: undefined,
            provider: selectedModel
          };
          
          const agentResponse = await callAgentAPI(synthContext, abortController.signal);
          const shouldContinue = await executeResponseAction(
            agentResponse, 
            addMessageToHistory, 
            abortController.signal
          );

          continueWorkflow = shouldContinue;

        } catch (error) {
          if (error instanceof Error && error.name === 'AbortError') {
            throw error;
          }
          const errorMessage: Message = {
            id: (Date.now() + iterationCount).toString(),
            content: "I'm having trouble processing your request. Let me try a different approach.",
            isUser: false,
            sender: 'system',
            timestamp: new Date(),
            isSystemMessage: true
          };
          addMessageToHistory(errorMessage);
          continueWorkflow = false;
        }
      }

      if (iterationCount >= MAX_ITERATIONS) {
        const maxIterationMessage: Message = {
          id: Date.now().toString(),
          content: "I've completed several steps but need to pause here. How can I help you next?",
          isUser: false,
          sender: 'system',
          timestamp: new Date(),
          isSystemMessage: true
        };
        addMessageToHistory(maxIterationMessage);
      }

    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        const cancelMessage: Message = {
          id: Date.now().toString(),
          content: "Workflow cancelled.",
          isUser: false,
          sender: 'system',
          timestamp: new Date(),
          isSystemMessage: true
        };
        onMessagesChange(prevMessages => [...prevMessages, cancelMessage]);
      } else {
        const errorMessage: Message = {
          id: Date.now().toString(),
          content: "I'm having trouble processing your request. Please try again.",
          isUser: false,
          sender: 'system',
          timestamp: new Date(),
          isSystemMessage: true
        };
        onMessagesChange(prevMessages => [...prevMessages, errorMessage]);
      }
    } finally {
      setIsInSynthLoop(false);
      abortControllerRef.current = null;
      continueWorkflowRef.current = false;
    }
  }, [
    callAgentAPI,
    executeResponseAction,
    mediaBinItemsRef,
    currentCompositionRef,
    selectedModel,
    onMessagesChange
  ]);

  const stopWorkflow = useCallback(() => {
    continueWorkflowRef.current = false;
    abortControllerRef.current?.abort();
  }, []);

  return {
    isInSynthLoop,
    runAgentWorkflow,
    stopWorkflow,
  };
}
