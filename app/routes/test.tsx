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
        "id": "clip-1",
        "startTimeInSeconds": 0,
        "endTimeInSeconds": 3,
        "element": {
          "elements": [
            "div;id:container;parent:root;display:flex;flexDirection:column;justifyContent:center;alignItems:center;width:100%;height:100%;backgroundColor:#1a1a2e",
            "h1;id:title;parent:container;text:Implicit Root System;fontSize:56px;color:#00d4ff;fontFamily:Arial, sans-serif;fontWeight:bold;textShadow:0 0 20px rgba(0, 212, 255, 0.5);marginBottom:30px",
            "p;id:subtitle;parent:container;text:AbsoluteFill root is automatic;fontSize:32px;color:#ffffff;fontFamily:Arial, sans-serif"
          ]
        }
      },
      {
        "id": "clip-2",
        "startTimeInSeconds": 3,
        "endTimeInSeconds": 6,
        "element": {
          "elements": [
            "div;id:box;parent:root;display:flex;justifyContent:center;alignItems:center;width:100%;height:100%;backgroundColor:#2e1a1a",
            "h2;id:message;parent:box;text:Second Clip with Animations!;fontSize:48px;color:#ff6b6b;fontWeight:bold",
            "div;id:animated-box;parent:box;width:100px;height:100px;backgroundColor:#4ecdc4;marginTop:30px;opacity:@animate[3,4,5,6]:[0,1,1,0];transform:@animate[3,4,5,6]:[translateY(50px),translateY(0px),translateY(0px),translateY(-50px)]"
          ]
        }
      },
      {
        "id": "clip-3",
        "startTimeInSeconds": 6,
        "endTimeInSeconds": 9,
        "element": {
          "elements": [
            "div;id:center;parent:root;display:flex;justifyContent:center;alignItems:center;flexDirection:column;width:100%;height:100%;backgroundColor:#1a2e1a",
            "SplitText;id:split1;parent:center;text:Animated Text Components;animateBy:letters;direction:top;delay:0.05;duration:0.3;fontSize:48px;color:#7bed9f;fontWeight:bold",
            "BlurText;id:blur1;parent:center;text:With blur effects;animateBy:words;direction:bottom;delay:0.1;duration:0.5;fontSize:32px;color:#ffffff;marginTop:20px"
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
          <h1 className="text-3xl font-bold mb-2">String Element Parser Test</h1>
          <p className="text-muted-foreground">
            Testing new semicolon-separated string format with @animate syntax
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Blueprint Input */}
          <Card>
            <CardHeader>
              <CardTitle>Blueprint JSON (String Format)</CardTitle>
              <CardDescription>
                Elements as semicolon-separated strings with @animate syntax for animations
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
