import React, { useState, useRef } from "react";
import type { PlayerRef } from "@remotion/player";
import { DynamicVideoPlayer } from "~/video-compositions/DynamicComposition";
import { calculateBlueprintDuration } from "~/video-compositions/executeClipElement";
import type { CompositionBlueprint } from "~/video-compositions/BlueprintTypes";
import { Button } from "~/components/ui/button";
import { Textarea } from "~/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "~/components/ui/card";
import { Alert, AlertDescription } from "~/components/ui/alert";
import { Play, Pause, Square, AlertCircle } from "lucide-react";

const defaultBlueprintExample = `[
  {
    "clips": [
      {
        "id": "splittext-test",
        "startTimeInSeconds": 0,
        "endTimeInSeconds": 3,
        "element": {
          "name": "div",
          "props": {
            "backgroundColor": "#1a1a2e",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "center",
            "alignItems": "center",
            "width": "100%",
            "height": "100%"
          },
          "children": [
            {
              "name": "SplitText",
              "props": {
                "text": "Split Text Animation",
                "animateBy": "letters",
                "direction": "top",
                "delay": 0.05,
                "duration": 0.5,
                "fontSize": "56px",
                "color": "#00d4ff",
                "fontFamily": "Arial, sans-serif",
                "fontWeight": "bold",
                "textShadow": "0 0 20px rgba(0, 212, 255, 0.5)",
                "marginBottom": "30px"
              }
            },
            {
              "name": "SplitText",
              "props": {
                "text": "Each letter animates in",
                "animateBy": "words",
                "direction": "bottom",
                "delay": 0.15,
                "duration": 0.6,
                "fontSize": "32px",
                "color": "#ffffff",
                "fontFamily": "Arial, sans-serif"
              }
            }
          ]
        }
      },
      {
        "id": "blurtext-test",
        "startTimeInSeconds": 3,
        "endTimeInSeconds": 6,
        "element": {
          "name": "div",
          "props": {
            "backgroundColor": "#1a1a2e",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "center",
            "alignItems": "center",
            "width": "100%",
            "height": "100%"
          },
          "children": [
            {
              "name": "BlurText",
              "props": {
                "text": "Blur Text Effect",
                "animateBy": "letters",
                "direction": "top",
                "delay": 0.08,
                "duration": 0.9,
                "fontSize": "56px",
                "color": "#ff6b6b",
                "fontFamily": "Arial, sans-serif",
                "fontWeight": "bold",
                "textShadow": "0 0 20px rgba(255, 107, 107, 0.5)",
                "marginBottom": "30px"
              }
            },
            {
              "name": "BlurText",
              "props": {
                "text": "Gradual unblur animation",
                "animateBy": "words",
                "direction": "bottom",
                "delay": 0.2,
                "duration": 0.9,
                "fontSize": "32px",
                "color": "#ffffff",
                "fontFamily": "Arial, sans-serif"
              }
            }
          ]
        }
      },
      {
        "id": "typewriter-test",
        "startTimeInSeconds": 6,
        "endTimeInSeconds": 10,
        "element": {
          "name": "div",
          "props": {
            "backgroundColor": "#1a1a2e",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "center",
            "alignItems": "center",
            "width": "100%",
            "height": "100%"
          },
          "children": [
            {
              "name": "TypewriterText",
              "props": {
                "text": "Typewriter Effect...",
                "typingSpeed": 15,
                "initialDelay": 0.5,
                "showCursor": true,
                "cursorCharacter": "|",
                "fontSize": "48px",
                "color": "#00ff88",
                "fontFamily": "monospace",
                "marginBottom": "30px"
              }
            }
          ]
        }
      },
      {
        "id": "shuffle-test",
        "startTimeInSeconds": 10,
        "endTimeInSeconds": 14,
        "element": {
          "name": "div",
          "props": {
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "center",
            "alignItems": "center",
            "width": "100%",
            "height": "100%",
            "gap": "40px"
          },
          "children": [
            {
              "name": "Shuffle",
              "props": {
                "text": "SHUFFLE FROM RIGHT",
                "shuffleDirection": "right",
                "duration": 1.2,
                "delay": 0.5,
                "stagger": 0.04,
                "shuffleTimes": 4,
                "animationMode": "evenodd",
                "scrambleCharset": "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&*",
                "colorFrom": "#ff0066",
                "colorTo": "#00ffff",
                "fontSize": "48px",
                "fontWeight": "bold",
                "fontFamily": "monospace"
              }
            },
            {
              "name": "Shuffle",
              "props": {
                "text": "shuffle from left",
                "shuffleDirection": "left",
                "duration": 1.0,
                "delay": 1.8,
                "stagger": 0.03,
                "shuffleTimes": 3,
                "animationMode": "sequential",
                "fontSize": "36px",
                "color": "#ffff00",
                "fontFamily": "sans-serif"
              }
            }
          ]
        }
      },
      {
        "id": "gradient-test",
        "startTimeInSeconds": 14,
        "endTimeInSeconds": 18,
        "element": {
          "name": "div",
          "props": {
            "backgroundColor": "#1a1a2e",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "center",
            "alignItems": "center",
            "width": "100%",
            "height": "100%",
            "gap": "40px"
          },
          "children": [
            {
              "name": "GradientText",
              "props": {
                "text": "ANIMATED GRADIENT",
                "colors": ["#40ffaa", "#4079ff", "#40ffaa", "#4079ff", "#40ffaa"],
                "animationSpeed": 3,
                "showBorder": false,
                "fontSize": "56px",
                "fontWeight": "bold",
                "fontFamily": "Arial, sans-serif"
              }
            },
            {
              "name": "GradientText",
              "props": {
                "text": "with border glow",
                "colors": ["#ff6b6b", "#feca57", "#48dbfb", "#ff9ff3"],
                "animationSpeed": 4,
                "showBorder": true,
                "fontSize": "36px",
                "fontWeight": "600",
                "fontFamily": "Arial, sans-serif"
              }
            }
          ]
        }
      },
      {
        "id": "decrypted-test",
        "startTimeInSeconds": 18,
        "endTimeInSeconds": 22,
        "element": {
          "name": "div",
          "props": {
            "backgroundColor": "#1a1a2e",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "center",
            "alignItems": "center",
            "width": "100%",
            "height": "100%",
            "gap": "40px"
          },
          "children": [
            {
              "name": "DecryptedText",
              "props": {
                "text": "DECRYPTING MESSAGE",
                "speed": 8,
                "sequential": true,
                "revealDirection": "start",
                "delay": 0.5,
                "fontSize": "56px",
                "fontWeight": "bold",
                "fontFamily": "monospace",
                "color": "#00ff88"
              }
            },
            {
              "name": "DecryptedText",
              "props": {
                "text": "CENTER REVEAL",
                "speed": 6,
                "sequential": true,
                "revealDirection": "center",
                "delay": 2,
                "fontSize": "42px",
                "fontWeight": "600",
                "fontFamily": "monospace",
                "color": "#4079ff"
              }
            }
          ]
        }
      },
      {
        "id": "truefocus-test",
        "startTimeInSeconds": 22,
        "endTimeInSeconds": 28,
        "element": {
          "name": "div",
          "props": {
            "backgroundColor": "#0a0a0a",
            "display": "flex",
            "justifyContent": "center",
            "alignItems": "center",
            "width": "100%",
            "height": "100%"
          },
          "children": [
            {
              "name": "TrueFocus",
              "props": {
                "text": "TRUE FOCUS ANIMATION EFFECT",
                "blurAmount": 8,
                "borderColor": "#00ff00",
                "glowColor": "rgba(0, 255, 0, 0.6)",
                "animationDuration": 0.6,
                "pauseBetweenAnimations": 0.8,
                "delay": 0.5,
                "fontSize": "48px",
                "fontWeight": "bold",
                "fontFamily": "monospace",
                "color": "#ffffff"
              }
            }
          ]
        }
      },
      {
        "id": "glitch-test",
        "startTimeInSeconds": 28,
        "endTimeInSeconds": 34,
        "element": {
          "name": "div",
          "props": {
            "backgroundColor": "#060010",
            "display": "flex",
            "justifyContent": "center",
            "alignItems": "center",
            "width": "100%",
            "height": "100%"
          },
          "children": [
            {
              "name": "GlitchText",
              "props": {
                "text": "GLITCH",
                "speed": 1.5,
                "enableShadows": true,
                "shadowColors": {
                  "red": "#ff0000",
                  "cyan": "#00ffff"
                },
                "glitchIntensity": 10,
                "delay": 0.3,
                "fontSize": "128px",
                "fontWeight": "900",
                "color": "#ffffff",
                "backgroundColor": "#060010"
              }
            }
          ]
        }
      }
    ]
  }
]`;

export default function TestPage() {
  const [blueprintText, setBlueprintText] = useState(defaultBlueprintExample);
  const [currentBlueprint, setCurrentBlueprint] = useState<CompositionBlueprint | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const playerRef = useRef<PlayerRef>(null);

  const parseAndSetBlueprint = () => {
    try {
      const parsed = JSON.parse(blueprintText);
      setCurrentBlueprint(parsed);
      setError(null);
    } catch (err) {
      setError("Invalid JSON format. Please check your blueprint syntax.");
      setCurrentBlueprint(null);
    }
  };

  const handlePlay = () => {
    if (playerRef.current) {
      if (isPlaying) {
        playerRef.current.pause();
      } else {
        playerRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleStop = () => {
    if (playerRef.current) {
      playerRef.current.pause();
      playerRef.current.seekTo(0);
      setIsPlaying(false);
    }
  };

  const duration = currentBlueprint ? calculateBlueprintDuration(currentBlueprint) : 10;
  const totalClips = currentBlueprint ? currentBlueprint.reduce((acc, track) => acc + track.clips.length, 0) : 0;

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Blueprint Test Player</h1>
          <p className="text-muted-foreground">
            Paste your composition blueprint JSON and preview it instantly
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Blueprint Input */}
          <Card>
            <CardHeader>
              <CardTitle>Composition Blueprint</CardTitle>
              <CardDescription>
                Paste your blueprint JSON here and click "Load Blueprint" to preview
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                value={blueprintText}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setBlueprintText(e.target.value)}
                placeholder="Paste your blueprint JSON here..."
                className="min-h-[400px] font-mono text-sm"
              />
              
              <div className="flex gap-2">
                <Button onClick={parseAndSetBlueprint}>
                  Load Blueprint
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => setBlueprintText(defaultBlueprintExample)}
                >
                  Load Example
                </Button>
              </div>

              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Video Player */}
          <Card>
            <CardHeader>
              <CardTitle>Preview Player</CardTitle>
              <CardDescription>
                {currentBlueprint 
                  ? `Duration: ${duration}s | ${totalClips} clips`
                  : "Load a blueprint to start previewing"
                }
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="aspect-video bg-black rounded-lg overflow-hidden">
                {currentBlueprint ? (
                  <DynamicVideoPlayer
                    blueprint={currentBlueprint}
                    compositionWidth={640}
                    compositionHeight={360}
                    playerRef={playerRef}
                    durationInFrames={duration * 30}
                  />
                ) : (
                  <div className="flex items-center justify-center h-full text-muted-foreground">
                    <div className="text-center">
                      <div className="mb-2">No blueprint loaded</div>
                      <div className="text-sm">Load a blueprint to see the preview</div>
                    </div>
                  </div>
                )}
              </div>

              {/* Player Controls */}
              <div className="flex gap-2 justify-center">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handlePlay}
                  disabled={!currentBlueprint}
                >
                  {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                  {isPlaying ? 'Pause' : 'Play'}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleStop}
                  disabled={!currentBlueprint}
                >
                  <Square className="h-4 w-4" />
                  Stop
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Blueprint Info */}
        {currentBlueprint && (
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Blueprint Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div>
                  <div className="font-medium">Total Clips</div>
                  <div className="text-muted-foreground">{totalClips}</div>
                </div>
                <div>
                  <div className="font-medium">Duration</div>
                  <div className="text-muted-foreground">{duration} seconds</div>
                </div>
                <div>
                  <div className="font-medium">Total Frames</div>
                  <div className="text-muted-foreground">{duration * 30} frames (30fps)</div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
