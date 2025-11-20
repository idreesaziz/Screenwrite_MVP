import React from "react";
import { Bot, Sparkles, Code, Zap, DollarSign } from "lucide-react";
import { Button } from "~/components/ui/button";

interface ProviderPairing {
  id: string;
  editEngine: "gemini" | "claude";
  agent: "gemini" | "gemini-3-low" | "gemini-3-high" | "claude" | "openai";
  label: string;
  description: string;
  recommended?: boolean;
  best?: boolean;
  costLevel: 1 | 2 | 3 | 4 | 5; // 1 = cheapest, 5 = most expensive
  speedLevel: 1 | 2 | 3; // 1 = fastest, 3 = slowest
}

const PROVIDER_PAIRINGS: ProviderPairing[] = [
  {
    id: "gemini-gemini",
    editEngine: "gemini",
    agent: "gemini",
    label: "Gemini 2.5 Flash + Gemini 2.5 Flash",
    description: "Most affordable. Fast and reliable for quick iterations.",
    recommended: true,
    costLevel: 1,
    speedLevel: 1,
  },
  {
    id: "gemini-gemini-3-low",
    editEngine: "gemini",
    agent: "gemini-3-low",
    label: "Gemini 2.5 Flash + Gemini 3 Pro (Low Thinking)",
    description: "Affordable. Advanced reasoning with controlled thinking budget.",
    costLevel: 2,
    speedLevel: 1,
  },
  {
    id: "gemini-gemini-3-high",
    editEngine: "gemini",
    agent: "gemini-3-high",
    label: "Gemini 2.5 Flash + Gemini 3 Pro (High Thinking)",
    description: "Mid-range. Maximum reasoning with extended thinking.",
    costLevel: 3,
    speedLevel: 2,
  },
  {
    id: "gemini-claude",
    editEngine: "gemini",
    agent: "claude",
    label: "Gemini 2.5 Flash + Claude Sonnet 4.5",
    description: "Affordable. Balanced speed with better reasoning.",
    costLevel: 2,
    speedLevel: 1,
  },
  {
    id: "claude-gemini",
    editEngine: "claude",
    agent: "gemini",
    label: "Claude Sonnet 4.5 + Gemini 2.5 Flash",
    description: "Mid-range. Faster edits with precise Claude processing.",
    costLevel: 2,
    speedLevel: 2,
  },
  {
    id: "claude-gemini-3-high",
    editEngine: "claude",
    agent: "gemini-3-high",
    label: "Claude Sonnet 4.5 + Gemini 3 Pro (High)",
    description: "Premium. Claude edits with cutting-edge Gemini 3 reasoning.",
    best: true,
    costLevel: 4,
    speedLevel: 2,
  },
  {
    id: "claude-claude",
    editEngine: "claude",
    agent: "claude",
    label: "Claude Sonnet 4.5 + Claude Sonnet 4.5",
    description: "Premium. Maximum quality and reasoning capability.",
    costLevel: 3,
    speedLevel: 2,
  },
  {
    id: "claude-gpt",
    editEngine: "claude",
    agent: "openai",
    label: "Claude Sonnet 4.5 + GPT-4.1",
    description: "Premium+. Solid quality but expensive and slower.",
    costLevel: 4,
    speedLevel: 3,
  },
];

interface ProviderPairingModalProps {
  isOpen: boolean;
  onSelect: (editProvider: "gemini" | "claude", agentProvider: "gemini" | "gemini-3-low" | "gemini-3-high" | "claude" | "openai") => void;
}

export function ProviderPairingModal({ isOpen, onSelect }: ProviderPairingModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[100]">
      <div className="bg-background border border-border rounded-lg shadow-2xl max-w-2xl w-full mx-4 overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-border/50 bg-background/95">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
              <Sparkles className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h2 className="text-lg font-semibold">Experimental AI Models</h2>
              <p className="text-sm text-muted-foreground">
                Test different foundation models for agentic layer and AI editing engine
              </p>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 max-h-[60vh] overflow-y-auto">
          <div className="grid gap-3">
            {PROVIDER_PAIRINGS.map((pairing) => (
              <button
                key={pairing.id}
                onClick={() => onSelect(pairing.editEngine, pairing.agent)}
                className="relative w-full text-left p-4 rounded-lg border border-border/50 hover:border-primary/50 hover:bg-accent/50 transition-all group"
              >
                {pairing.recommended && (
                  <div className="absolute top-2 right-2">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-primary/10 text-primary rounded-full">
                      <Sparkles className="h-3 w-3" />
                      Recommended
                    </span>
                  </div>
                )}
                
                {pairing.best && (
                  <div className="absolute top-2 right-2">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-amber-500/10 text-amber-600 dark:text-amber-400 rounded-full">
                      <Sparkles className="h-3 w-3" />
                      Best
                    </span>
                  </div>
                )}
                
                <div className="flex items-start gap-3">
                  <div className="flex gap-2 mt-1">
                    <div className="w-6 h-6 rounded bg-primary/10 flex items-center justify-center">
                      <Code className="h-3.5 w-3.5 text-primary" />
                    </div>
                    <div className="w-6 h-6 rounded bg-accent flex items-center justify-center">
                      <Bot className="h-3.5 w-3.5 text-muted-foreground" />
                    </div>
                  </div>
                  
                  <div className="flex-1">
                    <h3 className="font-medium text-sm mb-1 group-hover:text-primary transition-colors">
                      {pairing.label}
                    </h3>
                    <p className="text-xs text-muted-foreground mb-2">
                      {pairing.description}
                    </p>
                    
                    {/* Cost and Speed indicators */}
                    <div className="flex items-center gap-4 text-xs">
                      <div className="flex items-center gap-1">
                        <DollarSign className="h-3 w-3 text-muted-foreground" />
                        <div className="flex gap-0.5">
                          {[1, 2, 3, 4, 5].map((level) => (
                            <div
                              key={level}
                              className={`w-1.5 h-3 rounded-sm ${
                                level <= pairing.costLevel
                                  ? "bg-primary/60"
                                  : "bg-muted"
                              }`}
                            />
                          ))}
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-1">
                        <Zap className="h-3 w-3 text-muted-foreground" />
                        <div className="flex gap-0.5">
                          {[1, 2, 3].map((level) => (
                            <div
                              key={level}
                              className={`w-1.5 h-3 rounded-sm ${
                                level <= pairing.speedLevel
                                  ? "bg-amber-500/60"
                                  : "bg-muted"
                              }`}
                            />
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-border/50 bg-muted/30">
          <div className="flex items-center gap-3 text-xs text-muted-foreground flex-wrap">
            <div className="flex items-center gap-1">
              <DollarSign className="h-3 w-3" />
              <span>Cost</span>
            </div>
            <span className="text-border">•</span>
            <div className="flex items-center gap-1">
              <Zap className="h-3 w-3" />
              <span>Speed</span>
            </div>
            <span className="text-border mx-1">|</span>
            <span className="text-muted-foreground/70">You can change this anytime in chat settings</span>
          </div>
        </div>
      </div>
    </div>
  );
}
