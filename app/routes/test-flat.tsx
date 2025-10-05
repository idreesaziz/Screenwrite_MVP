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
            {
              "id": "root",
              "name": "AbsoluteFill",
              "parentId": null,
              "props": {
                "backgroundColor": "#1a1a2e"
              }
            },
            {
              "id": "container",
              "name": "div",
              "parentId": "root",
              "props": {
                "display": "flex",
                "flexDirection": "column",
                "justifyContent": "center",
                "alignItems": "center",
                "width": "100%",
                "height": "100%"
              }
            },
            {
              "id": "title",
              "name": "h1",
              "parentId": "container",
              "props": {
                "fontSize": "56px",
                "color": "#00d4ff",
                "fontFamily": "Arial, sans-serif",
                "fontWeight": "bold",
                "textShadow": "0 0 20px rgba(0, 212, 255, 0.5)",
                "marginBottom": "30px"
              },
              "text": "Flat Element Structure"
            },
            {
              "id": "subtitle",
              "name": "p",
              "parentId": "container",
              "props": {
                "fontSize": "32px",
                "color": "#ffffff",
                "fontFamily": "Arial, sans-serif"
              },
              "text": "Using parentId references instead of nested children"
            }
          ]
        }
      },
      {
        "id": "clip-2",
        "startTimeInSeconds": 3,
        "endTimeInSeconds": 6,
        "element": {
          "elements": [
            {
              "id": "root2",
              "name": "AbsoluteFill",
              "parentId": null,
              "props": {
                "backgroundColor": "#2e1a1a"
              }
            },
            {
              "id": "box",
              "name": "div",
              "parentId": "root2",
              "props": {
                "display": "flex",
                "justifyContent": "center",
                "alignItems": "center",
                "width": "100%",
                "height": "100%"
              }
            },
            {
              "id": "message",
              "name": "h2",
              "parentId": "box",
              "props": {
                "fontSize": "48px",
                "color": "#ff6b6b",
                "fontWeight": "bold"
              },
              "text": "Second Clip!"
            }
          ]
        }
      }
    ]
  }
]`;

export default function TestFlatPage() {
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
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Flat Blueprint Test Page</h1>
          <p className="text-gray-400">Test flat element structure with parentId references</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Blueprint Editor */}
          <Card className="bg-gray-800 border-gray-700">
            <CardHeader>
              <CardTitle className="text-white">Blueprint JSON (Flat Structure)</CardTitle>
              <CardDescription className="text-gray-400">
                Edit the blueprint JSON and click "Load Blueprint" to test
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                value={blueprintText}
                onChange={(e) => setBlueprintText(e.target.value)}
                className="font-mono text-sm h-96 bg-gray-900 text-white border-gray-700"
                placeholder="Enter blueprint JSON..."
              />
              <Button
                onClick={parseAndSetBlueprint}
                className="w-full bg-blue-600 hover:bg-blue-700"
              >
                Load Blueprint
              </Button>
              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Player Preview */}
          <Card className="bg-gray-800 border-gray-700">
            <CardHeader>
              <CardTitle className="text-white">Preview</CardTitle>
              <CardDescription className="text-gray-400">
                {currentBlueprint ? `${totalClips} clips, ${duration.toFixed(1)}s total` : "Load a blueprint to preview"}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {currentBlueprint ? (
                <>
                  <div className="aspect-video bg-black rounded-lg overflow-hidden">
                    <DynamicVideoPlayer
                      blueprint={currentBlueprint}
                      fps={30}
                      playerRef={playerRef}
                      onPlay={() => setIsPlaying(true)}
                      onPause={() => setIsPlaying(false)}
                    />
                  </div>
                  <div className="flex gap-2">
                    <Button
                      onClick={handlePlay}
                      className="flex-1 bg-green-600 hover:bg-green-700"
                    >
                      {isPlaying ? <Pause className="mr-2 h-4 w-4" /> : <Play className="mr-2 h-4 w-4" />}
                      {isPlaying ? "Pause" : "Play"}
                    </Button>
                    <Button
                      onClick={handleStop}
                      className="flex-1 bg-red-600 hover:bg-red-700"
                    >
                      <Square className="mr-2 h-4 w-4" />
                      Stop
                    </Button>
                  </div>
                </>
              ) : (
                <div className="aspect-video bg-gray-900 rounded-lg flex items-center justify-center">
                  <p className="text-gray-500">No blueprint loaded</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
