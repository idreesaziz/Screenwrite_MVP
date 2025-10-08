/**
 * ConversationalSynth - Frontend interface for backend conversational AI agent
 * 
 * This handles:
 * 1. Calling backend /ai/agent endpoint
 * 2. Managing conversation state
 * 3. Streaming chat responses (optional feature)
 */

import type { MediaBinItem } from "../timeline/types";

export interface ConversationMessage {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
}

export interface SynthResponse {
  type: 'chat' | 'edit' | 'probe' | 'generate' | 'fetch' | 'sleep';
  content: string;
  referencedFiles?: string[]; // @-mentioned files
  fileName?: string; // For probe responses - can be media file from library OR YouTube URL
  question?: string; // For probe responses
  prompt?: string; // For generate responses - content generation prompt
  suggestedName?: string; // For generate responses - AI-chosen filename
  content_type?: 'image' | 'video'; // For generate responses - type of content to generate
  seedImageFileName?: string; // For generate video responses - filename of image to use as seed/reference
  query?: string; // For fetch responses - search query for stock videos
}

export interface SynthContext {
  messages: ConversationMessage[];
  currentComposition?: any; // Blueprint composition
  mediaLibrary: MediaBinItem[];
  compositionDuration?: number;
}

export class ConversationalSynth {
  constructor(apiKey?: string) {
    // API key is now handled globally in the file
    // This constructor is kept for compatibility
  }

  /**
   * Main entry point - call backend agent API
   */
  async processMessage(
    context: SynthContext
  ): Promise<SynthResponse> {
    console.log("🧠 ConversationalSynth: Processing conversation with", context.messages.length, "messages");
    
    const { apiUrl } = await import('~/utils/api');

    try {
      // Call backend agent endpoint
      const response = await fetch(apiUrl('/ai/agent', true), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: context.messages.map(msg => ({
            id: msg.id,
            content: msg.content,
            isUser: msg.isUser,
            timestamp: msg.timestamp.toISOString()
          })),
          currentComposition: context.currentComposition,
          mediaLibrary: context.mediaLibrary,
          compositionDuration: context.compositionDuration
        })
      });

      if (!response.ok) {
        throw new Error(`Backend agent API error: ${response.status}`);
      }

      const agentResponse = await response.json();
      
      console.log(`✅ Agent response type: ${agentResponse.type}`);
      
      return {
        type: agentResponse.type,
        content: agentResponse.content,
        fileName: agentResponse.fileName,
        question: agentResponse.question,
        prompt: agentResponse.prompt,
        suggestedName: agentResponse.suggestedName,
        content_type: agentResponse.content_type,
        seedImageFileName: agentResponse.seedImageFileName,
        query: agentResponse.query
      };

    } catch (error) {
      console.error("❌ Agent API call failed:", error);
      
      return {
        type: 'sleep',
        content: "There was an API error. Please try again later."
      };
    }
  }
}
