import type { MediaBinItem } from "~/components/editor/timeline/types";

// Sender type for conversation messages
export type ConversationSender = 'user' | 'assistant' | 'system' | 'tool';

// Message format for conversation history sent to backend
export interface ConversationMessage {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
  sender: ConversationSender;
}

// Response from the agent API
export interface SynthResponse {
  type: 'info' | 'sleep' | 'fetch' | 'generate' | 'probe' | 'edit';
  content: string;
  query?: string;
  prompt?: string;
  suggestedName?: string;
  content_type?: 'image' | 'video' | 'logo' | 'audio';
  seedImageFileName?: string;
  voice_settings?: {
    voice_id?: string;
    language_code?: string;
    speaking_rate?: number;
    pitch?: number;
  };
  files?: Array<{ fileName: string; question: string }>;
}

// Context passed to the agent API
export interface SynthContext {
  messages: ConversationMessage[];
  currentComposition?: object;
  mediaLibrary: MediaBinItem[];
  compositionDuration?: number;
  provider?: string;
}

// Word/sentence timestamp from audio generation
export interface WordTimestamp {
  word: string;
  start: number;
  end: number;
}

// Video option from stock search
export interface VideoOption {
  id: string;
  title: string;
  duration: string;
  description: string;
  thumbnailUrl: string;
  downloadUrl: string;
  pexelsUrl: string;
  width?: number;
  height?: number;
  durationInSeconds?: number;
}

// Composition diff for showing changes
export interface CompositionDiff {
  before: string;
  after: string;
}

// Message in the chat UI
export interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
  sender?: ConversationSender;
  isSystemMessage?: boolean;
  isExplanationMode?: boolean;
  isAnalysisResult?: boolean;
  isVideoSelection?: boolean;
  videoOptions?: VideoOption[];
  hasRetryButton?: boolean;
  retryData?: {
    originalMessage: string;
  };
  word_timestamps?: WordTimestamp[];
  compositionDiff?: CompositionDiff;
  alreadyInUI?: boolean;
}

// Generation error state
export interface GenerationError {
  hasError: boolean;
  errorMessage: string;
  canRetry: boolean;
}

// Props for ChatBox component
export interface ChatBoxProps {
  messages: Message[];
  onMessagesChange: React.Dispatch<React.SetStateAction<Message[]>>;
  mediaBinItems: MediaBinItem[];
  mediaBinItemsRef: React.MutableRefObject<MediaBinItem[]>;
  currentCompositionRef: React.MutableRefObject<string | undefined>;
  timelineState?: object;
  handleDropOnTrack: (item: MediaBinItem, trackId: string, dropLeftPx: number) => void;
  getToken: () => Promise<string | null>;
  onGenerateComposition?: (
    instruction: string,
    mediaLibrary: MediaBinItem[],
    agentProvider: string,
    editProvider: string,
    signal?: AbortSignal
  ) => Promise<boolean>;
  onAddGeneratedImage?: (mediaItem: MediaBinItem) => Promise<void>;
  isStandalonePreview?: boolean;
  initialAgentProvider?: string;
  initialEditProvider?: string;
  isGeneratingComposition?: boolean;
  generationError?: GenerationError;
  onRetryFix?: () => Promise<boolean>;
  onClearError?: () => void;
  isMinimized?: boolean;
  onToggleMinimize?: () => void;
  className?: string;
}
