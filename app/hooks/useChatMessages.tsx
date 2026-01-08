import { useState, useCallback } from "react";
import type React from "react";

export interface DiffLine {
  type: 'same' | 'removed' | 'added';
  content: string;
}

export interface UseChatMessagesReturn {
  collapsedMessages: Set<string>;
  toggleMessageCollapsed: (messageId: string) => void;
  createDiff: (before: string, after: string) => DiffLine[];
  formatText: (text: string) => React.ReactNode;
  formatTime: (date: Date) => string;
}

export function useChatMessages(): UseChatMessagesReturn {
  const [collapsedMessages, setCollapsedMessages] = useState<Set<string>>(new Set());

  const toggleMessageCollapsed = useCallback((messageId: string) => {
    setCollapsedMessages(prev => {
      const newSet = new Set(prev);
      if (newSet.has(messageId)) {
        newSet.delete(messageId);
      } else {
        newSet.add(messageId);
      }
      return newSet;
    });
  }, []);

  const createDiff = useCallback((before: string, after: string): DiffLine[] => {
    const beforeLines = before.split('\n');
    const afterLines = after.split('\n');
    
    const diffLines: DiffLine[] = [];
    
    let beforeIdx = 0;
    let afterIdx = 0;
    
    while (beforeIdx < beforeLines.length || afterIdx < afterLines.length) {
      const beforeLine = beforeLines[beforeIdx] || '';
      const afterLine = afterLines[afterIdx] || '';
      
      if (beforeLine === afterLine) {
        diffLines.push({ type: 'same', content: beforeLine });
        beforeIdx++;
        afterIdx++;
      } else {
        const beforeNext = beforeLines[beforeIdx + 1] || '';
        const afterNext = afterLines[afterIdx + 1] || '';
        
        if (beforeLine && afterLine && beforeNext === afterLine) {
          diffLines.push({ type: 'removed', content: beforeLine });
          beforeIdx++;
        } else if (beforeLine && afterLine && afterNext === beforeLine) {
          diffLines.push({ type: 'added', content: afterLine });
          afterIdx++;
        } else {
          if (beforeIdx < beforeLines.length) {
            diffLines.push({ type: 'removed', content: beforeLine });
            beforeIdx++;
          }
          if (afterIdx < afterLines.length) {
            diffLines.push({ type: 'added', content: afterLine });
            afterIdx++;
          }
        }
      }
    }
    
    return diffLines;
  }, []);

  const formatText = useCallback((text: string): React.ReactNode => {
    const parts = text.split(/(\*\*\*[^*]+\*\*\*|\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|^---+$|^#{1,6}\s+.+$)/gm);
    
    return parts.map((part, index) => {
      if (part.startsWith('***') && part.endsWith('***')) {
        return <strong key={index} className="font-bold italic">{part.slice(3, -3)}</strong>;
      } else if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={index} className="font-bold">{part.slice(2, -2)}</strong>;
      } else if (part.startsWith('*') && part.endsWith('*')) {
        return <em key={index} className="italic">{part.slice(1, -1)}</em>;
      } else if (part.startsWith('`') && part.endsWith('`')) {
        return <code key={index} className="bg-gray-200 dark:bg-gray-700 px-1 py-0.5 rounded text-xs font-mono">{part.slice(1, -1)}</code>;
      } else if (/^---+$/.test(part.trim())) {
        return <hr key={index} className="my-2 border-gray-300 dark:border-gray-600" />;
      } else if (/^#{1,6}\s+/.test(part)) {
        const level = part.match(/^(#{1,6})/)?.[1].length || 1;
        const content = part.replace(/^#{1,6}\s+/, '');
        if (level === 1) {
          return <h1 key={index} className="text-lg font-bold mt-2 mb-1">{content}</h1>;
        } else if (level === 2) {
          return <h2 key={index} className="text-base font-bold mt-2 mb-1">{content}</h2>;
        } else if (level === 3) {
          return <h3 key={index} className="text-sm font-semibold mt-1 mb-1">{content}</h3>;
        } else {
          return <h4 key={index} className="text-sm font-medium mt-1 mb-1">{content}</h4>;
        }
      } else {
        return part;
      }
    });
  }, []);

  const formatTime = useCallback((date: Date): string => {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }, []);

  return {
    collapsedMessages,
    toggleMessageCollapsed,
    createDiff,
    formatText,
    formatTime,
  };
}
