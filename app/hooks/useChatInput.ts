import { useState, useCallback, useRef, type RefObject } from "react";
import type { MediaBinItem } from "~/components/editor/timeline/types";

export interface UseChatInputOptions {
  mediaBinItems: MediaBinItem[];
  onSendMessage: (content: string, mentionedItems: MediaBinItem[], includeAllMedia: boolean) => void;
}

export interface UseChatInputReturn {
  // State
  inputValue: string;
  showMentions: boolean;
  mentionQuery: string;
  selectedMentionIndex: number;
  mentionedItems: MediaBinItem[];
  textareaHeight: number;
  filteredMentions: MediaBinItem[];
  
  // Refs
  inputRef: RefObject<HTMLTextAreaElement | null>;
  mentionsRef: RefObject<HTMLDivElement | null>;
  
  // Handlers
  handleInputChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  handleKeyPress: (e: React.KeyboardEvent, sendWithMedia: boolean) => void;
  insertMention: (item: MediaBinItem) => void;
  clearInput: () => void;
  setMentionedItems: React.Dispatch<React.SetStateAction<MediaBinItem[]>>;
}

export function useChatInput({
  mediaBinItems,
  onSendMessage,
}: UseChatInputOptions): UseChatInputReturn {
  const [inputValue, setInputValue] = useState("");
  const [showMentions, setShowMentions] = useState(false);
  const [mentionQuery, setMentionQuery] = useState("");
  const [selectedMentionIndex, setSelectedMentionIndex] = useState(0);
  const [cursorPosition, setCursorPosition] = useState(0);
  const [textareaHeight, setTextareaHeight] = useState(36);
  const [mentionedItems, setMentionedItems] = useState<MediaBinItem[]>([]);

  const inputRef = useRef<HTMLTextAreaElement>(null);
  const mentionsRef = useRef<HTMLDivElement>(null);

  // Filter media bin items based on mention query
  const filteredMentions = mediaBinItems.filter((item) =>
    item.name.toLowerCase().includes(mentionQuery.toLowerCase())
  );

  // Handle input changes and @ mention detection
  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    const cursorPos = e.target.selectionStart || 0;

    setInputValue(value);
    setCursorPosition(cursorPos);

    // Auto-resize textarea
    const textarea = e.target;
    textarea.style.height = "auto";
    const newHeight = Math.min(textarea.scrollHeight, 96);
    textarea.style.height = newHeight + "px";
    setTextareaHeight(newHeight);

    // Clean up mentioned items that are no longer in the text
    const mentionPattern = /@(\w+(?:\s+\w+)*)/g;
    const currentMentions = Array.from(value.matchAll(mentionPattern)).map(match => match[1]);
    setMentionedItems(prev => prev.filter(item => 
      currentMentions.some(mention => mention.toLowerCase() === item.name.toLowerCase())
    ));

    // Check for @ mentions
    const beforeCursor = value.slice(0, cursorPos);
    const lastAtIndex = beforeCursor.lastIndexOf("@");

    if (lastAtIndex !== -1) {
      const afterAt = beforeCursor.slice(lastAtIndex + 1);
      const isValidMention =
        (lastAtIndex === 0 || /\s/.test(beforeCursor[lastAtIndex - 1])) &&
        !afterAt.includes(" ");

      if (isValidMention) {
        setMentionQuery(afterAt);
        setShowMentions(true);
        setSelectedMentionIndex(0);
      } else {
        setShowMentions(false);
      }
    } else {
      setShowMentions(false);
    }
  }, []);

  // Insert mention into input
  const insertMention = useCallback((item: MediaBinItem) => {
    const beforeCursor = inputValue.slice(0, cursorPosition);
    const afterCursor = inputValue.slice(cursorPosition);
    const lastAtIndex = beforeCursor.lastIndexOf("@");

    const newValue =
      beforeCursor.slice(0, lastAtIndex) + `@${item.name} ` + afterCursor;
    setInputValue(newValue);
    setShowMentions(false);

    // Store the actual item reference
    setMentionedItems(prev => {
      if (!prev.find(existingItem => existingItem.id === item.id)) {
        return [...prev, item];
      }
      return prev;
    });

    // Focus back to input
    setTimeout(() => {
      inputRef.current?.focus();
      const newCursorPos = lastAtIndex + item.name.length + 2;
      inputRef.current?.setSelectionRange(newCursorPos, newCursorPos);
    }, 0);
  }, [inputValue, cursorPosition]);

  // Handle keyboard navigation in mentions and send
  const handleKeyPress = useCallback((e: React.KeyboardEvent, sendWithMedia: boolean) => {
    if (showMentions && filteredMentions.length > 0) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedMentionIndex((prev) =>
          prev < filteredMentions.length - 1 ? prev + 1 : 0
        );
        return;
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedMentionIndex((prev) =>
          prev > 0 ? prev - 1 : filteredMentions.length - 1
        );
        return;
      }
      if (e.key === "Enter") {
        e.preventDefault();
        insertMention(filteredMentions[selectedMentionIndex]);
        return;
      }
      if (e.key === "Escape") {
        e.preventDefault();
        setShowMentions(false);
        return;
      }
    }

    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (inputValue.trim()) {
        onSendMessage(inputValue.trim(), mentionedItems, sendWithMedia);
      }
    }
  }, [showMentions, filteredMentions, selectedMentionIndex, insertMention, inputValue, mentionedItems, onSendMessage]);

  // Clear input after sending
  const clearInput = useCallback(() => {
    setInputValue("");
    setMentionedItems([]);
    if (inputRef.current) {
      inputRef.current.style.height = "36px";
      setTextareaHeight(36);
    }
  }, []);

  return {
    inputValue,
    showMentions,
    mentionQuery,
    selectedMentionIndex,
    mentionedItems,
    textareaHeight,
    filteredMentions,
    inputRef,
    mentionsRef,
    handleInputChange,
    handleKeyPress,
    insertMention,
    clearInput,
    setMentionedItems,
  };
}
