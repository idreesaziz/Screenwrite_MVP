/**
 * SessionHistory component - Sidebar for managing chat sessions.
 * Shows list of past sessions with load/delete functionality.
 */

import React, { useState } from "react";
import { Plus, MessageSquare, Trash2, ChevronLeft, ChevronRight, Loader2 } from "lucide-react";
import { Button } from "../ui/button";
import { ScrollArea } from "../ui/scroll-area";
import { cn } from "../../lib/utils";
import type { SessionListItem } from "../../utils/sessionApi";

interface SessionHistoryProps {
  sessions: SessionListItem[];
  currentSessionId: string | null;
  isLoading: boolean;
  onNewSession: () => void;
  onLoadSession: (sessionId: string) => void;
  onDeleteSession: (sessionId: string) => void;
  className?: string;
}

export function SessionHistory({
  sessions,
  currentSessionId,
  isLoading,
  onNewSession,
  onLoadSession,
  onDeleteSession,
  className,
}: SessionHistoryProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const handleDelete = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (confirmDeleteId === sessionId) {
      // Second click - actually delete
      setDeletingId(sessionId);
      try {
        await onDeleteSession(sessionId);
      } finally {
        setDeletingId(null);
        setConfirmDeleteId(null);
      }
    } else {
      // First click - show confirmation
      setConfirmDeleteId(sessionId);
      // Reset confirmation after 3 seconds
      setTimeout(() => {
        setConfirmDeleteId(null);
      }, 3000);
    }
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      return "Today";
    } else if (diffDays === 1) {
      return "Yesterday";
    } else if (diffDays < 7) {
      return `${diffDays} days ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  // Group sessions by date
  const groupedSessions = sessions.reduce<Record<string, SessionListItem[]>>((groups, session) => {
    const dateKey = formatDate(session.created_at);
    if (!groups[dateKey]) {
      groups[dateKey] = [];
    }
    groups[dateKey].push(session);
    return groups;
  }, {});

  if (isCollapsed) {
    return (
      <div className={cn("w-12 flex flex-col items-center py-4 border-r border-gray-800 bg-gray-950", className)}>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setIsCollapsed(false)}
          className="mb-4 text-gray-400 hover:text-white hover:bg-gray-800"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={onNewSession}
          className="text-gray-400 hover:text-white hover:bg-gray-800"
        >
          <Plus className="h-4 w-4" />
        </Button>
      </div>
    );
  }

  return (
    <div className={cn("w-64 flex flex-col border-r border-gray-800 bg-gray-950", className)}>
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-gray-800">
        <h2 className="text-sm font-medium text-gray-200">History</h2>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            onClick={onNewSession}
            className="h-7 w-7 text-gray-400 hover:text-white hover:bg-gray-800"
            title="New session"
          >
            <Plus className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsCollapsed(true)}
            className="h-7 w-7 text-gray-400 hover:text-white hover:bg-gray-800"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Session List */}
      <ScrollArea className="flex-1">
        {isLoading && sessions.length === 0 ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin text-gray-500" />
          </div>
        ) : sessions.length === 0 ? (
          <div className="p-4 text-center text-sm text-gray-500">
            No sessions yet
          </div>
        ) : (
          <div className="py-2">
            {Object.entries(groupedSessions).map(([dateKey, dateSession]) => (
              <div key={dateKey}>
                <div className="px-3 py-2 text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {dateKey}
                </div>
                {dateSession.map((session) => (
                  <div
                    key={session.id}
                    onClick={() => onLoadSession(session.id)}
                    className={cn(
                      "group flex items-center gap-2 px-3 py-2 mx-2 rounded-md cursor-pointer transition-colors",
                      session.id === currentSessionId
                        ? "bg-gray-800 text-white"
                        : "text-gray-300 hover:bg-gray-800/50"
                    )}
                  >
                    <MessageSquare className="h-4 w-4 flex-shrink-0 text-gray-500" />
                    <span className="flex-1 truncate text-sm">{session.title}</span>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={(e) => handleDelete(session.id, e)}
                      disabled={deletingId === session.id}
                      className={cn(
                        "h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity",
                        confirmDeleteId === session.id
                          ? "text-red-500 hover:text-red-400 opacity-100"
                          : "text-gray-500 hover:text-gray-300"
                      )}
                    >
                      {deletingId === session.id ? (
                        <Loader2 className="h-3 w-3 animate-spin" />
                      ) : (
                        <Trash2 className="h-3 w-3" />
                      )}
                    </Button>
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
      </ScrollArea>
    </div>
  );
}
