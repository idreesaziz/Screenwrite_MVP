/**
 * SessionHistory component - Sidebar for managing chat sessions.
 * Shows list of past sessions with load/delete functionality.
 */

import React, { useState } from "react";
import { Plus, MessageSquare, Trash2, ChevronLeft, ChevronRight, Loader2, History, Settings } from "lucide-react";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { cn } from "../../lib/utils";
import type { SessionListItem } from "../../utils/sessionApi";

interface SessionHistoryProps {
  sessions: SessionListItem[];
  currentSessionId: string | null;
  isLoading: boolean;
  onNewSession: () => void;
  onLoadSession: (sessionId: string) => void;
  onDeleteSession: (sessionId: string) => void;
  onOpenSettings: () => void;
  className?: string;
}

export function SessionHistory({
  sessions,
  currentSessionId,
  isLoading,
  onNewSession,
  onLoadSession,
  onDeleteSession,
  onOpenSettings,
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
      <div className={cn(
        "w-10 flex flex-col items-center py-2 border-r border-border/50 bg-background",
        className
      )}>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsCollapsed(false)}
          className="h-7 w-7 p-0 text-muted-foreground hover:text-foreground hover:bg-accent/50"
          title="Expand history"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
        <div className="my-2 w-6 h-px bg-border/50" />
        <Button
          variant="ghost"
          size="sm"
          onClick={onNewSession}
          className="h-7 w-7 p-0 text-muted-foreground hover:text-foreground hover:bg-accent/50"
          title="New session"
        >
          <Plus className="h-4 w-4" />
        </Button>
        <div className="flex-1" />
        <div className="my-2 w-6 h-px bg-border/50" />
        <Button
          variant="ghost"
          size="sm"
          onClick={onOpenSettings}
          className="h-7 w-7 p-0 text-muted-foreground hover:text-foreground hover:bg-accent/50"
          title="Settings"
        >
          <Settings className="h-4 w-4" />
        </Button>
      </div>
    );
  }

  return (
    <div className={cn(
      "w-56 flex flex-col border-r border-border/50 bg-background",
      className
    )}>
      {/* Compact Header */}
      <div className="p-2 border-b border-border/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <History className="h-3.5 w-3.5 text-muted-foreground" />
            <h3 className="text-xs font-medium text-foreground">History</h3>
          </div>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={onNewSession}
              className="h-6 px-2 text-xs text-muted-foreground hover:text-foreground"
              title="New session"
            >
              <Plus className="h-3 w-3 mr-1" />
              New
            </Button>
            <Badge variant="secondary" className="text-xs h-4 px-1.5 font-mono">
              {sessions.length}
            </Badge>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsCollapsed(true)}
              className="h-6 w-6 p-0 text-muted-foreground hover:text-foreground"
              title="Collapse"
            >
              <ChevronLeft className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      </div>

      {/* Session List */}
      <div className="flex-1 overflow-y-auto p-1.5 space-y-0.5 panel-scrollbar">
        {isLoading && sessions.length === 0 ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
          </div>
        ) : sessions.length === 0 ? (
          <div className="p-3 text-center text-xs text-muted-foreground">
            No sessions yet
          </div>
        ) : (
          <>
            {Object.entries(groupedSessions).map(([dateKey, dateSessions]) => (
              <div key={dateKey}>
                <div className="px-2 py-1.5 text-[10px] font-medium text-muted-foreground uppercase tracking-wider">
                  {dateKey}
                </div>
                {dateSessions.map((session) => (
                  <div
                    key={session.id}
                    onClick={() => onLoadSession(session.id)}
                    className={cn(
                      "group flex items-center gap-2 px-2 py-1.5 rounded-md cursor-pointer transition-colors",
                      session.id === currentSessionId
                        ? "bg-accent text-foreground"
                        : "text-muted-foreground hover:bg-accent/50 hover:text-foreground"
                    )}
                  >
                    <MessageSquare className="h-3.5 w-3.5 flex-shrink-0" />
                    <span className="flex-1 truncate text-xs">{session.title}</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => handleDelete(session.id, e)}
                      disabled={deletingId === session.id}
                      className={cn(
                        "h-5 w-5 p-0 opacity-0 group-hover:opacity-100 transition-opacity",
                        confirmDeleteId === session.id
                          ? "text-destructive hover:text-destructive opacity-100"
                          : "text-muted-foreground hover:text-foreground"
                      )}
                      title={confirmDeleteId === session.id ? "Click again to confirm" : "Delete"}
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
          </>
        )}
      </div>

      {/* Settings Footer */}
      <div className="p-2 border-t border-border/50">
        <Button
          variant="ghost"
          size="sm"
          onClick={onOpenSettings}
          className="w-full h-7 text-xs justify-start gap-2 text-muted-foreground hover:text-foreground"
        >
          <Settings className="h-3.5 w-3.5" />
          Settings
        </Button>
      </div>
    </div>
  );
}
