/**
 * SettingsModal - Modal for app settings including model selection.
 */

import React from "react";
import { X, Settings, Sparkles, ChevronDown, Check, Wand2 } from "lucide-react";
import { Button } from "~/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "~/components/ui/dropdown-menu";
import type { AgentProvider, EditProvider } from "./providerTypes";

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedModel: AgentProvider;
  onModelChange: (model: AgentProvider) => void;
  selectedEditProvider: EditProvider;
  onEditProviderChange: (provider: EditProvider) => void;
}

const AGENT_MODEL_OPTIONS: { value: AgentProvider; label: string }[] = [
  { value: "gemini", label: "Gemini 3 Flash" },
  { value: "gemini-3-low", label: "Gemini 3 Low" },
  { value: "gemini-3-high", label: "Gemini 3 High" },
  { value: "claude", label: "Claude" },
  { value: "openai", label: "GPT-4.1" },
];

const EDIT_PROVIDER_OPTIONS: { value: EditProvider; label: string }[] = [
  { value: "gemini", label: "Gemini 3 Flash" },
  { value: "gemini-3-low", label: "Gemini 3 Low" },
  { value: "gemini-3-high", label: "Gemini 3 High" },
  { value: "claude", label: "Claude" },
];

export function SettingsModal({
  isOpen,
  onClose,
  selectedModel,
  onModelChange,
  selectedEditProvider,
  onEditProviderChange,
}: SettingsModalProps) {
  if (!isOpen) return null;

  const selectedModelLabel = AGENT_MODEL_OPTIONS.find(m => m.value === selectedModel)?.label || "Select model";
  const selectedEditLabel = EDIT_PROVIDER_OPTIONS.find(m => m.value === selectedEditProvider)?.label || "Select provider";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative z-10 w-full max-w-md bg-background border border-border rounded-lg shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center gap-2">
            <Settings className="h-4 w-4 text-muted-foreground" />
            <h2 className="text-sm font-medium">Settings</h2>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="h-7 w-7 p-0 text-muted-foreground hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-5">
          {/* Agent Model Selection */}
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm font-medium text-foreground">
              <Sparkles className="h-3.5 w-3.5 text-muted-foreground" />
              Agent Model
            </label>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" className="w-full justify-between h-9 text-sm">
                  {selectedModelLabel}
                  <ChevronDown className="h-4 w-4 ml-2 text-muted-foreground" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="w-[calc(100%-2rem)]">
                {AGENT_MODEL_OPTIONS.map((option) => (
                  <DropdownMenuItem
                    key={option.value}
                    onClick={() => onModelChange(option.value)}
                    className="flex items-center justify-between text-sm"
                  >
                    {option.label}
                    {selectedModel === option.value && (
                      <Check className="h-4 w-4 text-primary" />
                    )}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
            <p className="text-xs text-muted-foreground">
              AI model for chat responses and video generation.
            </p>
          </div>

          {/* Edit Engine Provider */}
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm font-medium text-foreground">
              <Wand2 className="h-3.5 w-3.5 text-muted-foreground" />
              Edit Engine
            </label>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" className="w-full justify-between h-9 text-sm">
                  {selectedEditLabel}
                  <ChevronDown className="h-4 w-4 ml-2 text-muted-foreground" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="w-[calc(100%-2rem)]">
                {EDIT_PROVIDER_OPTIONS.map((option) => (
                  <DropdownMenuItem
                    key={option.value}
                    onClick={() => onEditProviderChange(option.value)}
                    className="flex items-center justify-between text-sm"
                  >
                    {option.label}
                    {selectedEditProvider === option.value && (
                      <Check className="h-4 w-4 text-primary" />
                    )}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
            <p className="text-xs text-muted-foreground">
              AI model for editing and refining compositions.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end p-4 border-t border-border">
          <Button variant="default" size="sm" onClick={onClose}>
            Done
          </Button>
        </div>
      </div>
    </div>
  );
}
