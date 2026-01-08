import { useState, useCallback } from "react";
import axios from "axios";
import { toast } from "sonner";
import { apiUrl } from "~/lib/api";
import {
  calculateBlueprintDuration,
  ensureMinimumTracks,
  type CompositionBlueprint,
} from "~/composition";
import type { MediaBinItem } from "~/components/editor/timeline/types";

interface PreviewSettings {
  width: number;
  height: number;
  backgroundColor: string;
  fps: number;
}

interface AIGenerationState {
  isGenerating: boolean;
}

interface AIGenerationActions {
  generateComposition: (
    userRequest: string,
    mediaBinItems: MediaBinItem[],
    modelType?: string,
    provider?: string,
    signal?: AbortSignal
  ) => Promise<boolean>;
  addGeneratedImage: (item: MediaBinItem) => void;
}

const MODEL_NAME_MAP: Record<string, string> = {
  gemini: "gemini-3-flash-preview",
  openai: "gpt-4o-mini"
};

const DEFAULT_PREVIEW_SETTINGS: PreviewSettings = {
  width: 1920,
  height: 1080,
  backgroundColor: "#000000",
  fps: 30
};

export function useAIGeneration(
  currentComposition: CompositionBlueprint,
  onCompositionUpdate: (composition: CompositionBlueprint) => void,
  onDurationUpdate: (frames: number) => void,
  onMediaBinAdd: (item: MediaBinItem) => void,
  getToken: () => Promise<string | null>,
  previewSettings: PreviewSettings = DEFAULT_PREVIEW_SETTINGS
): [AIGenerationState, AIGenerationActions] {
  const [isGenerating, setIsGenerating] = useState(false);

  const generateComposition = useCallback(async (
    userRequest: string,
    mediaBinItems: MediaBinItem[],
    modelType: string = "gemini",
    provider: string = "gemini",
    signal?: AbortSignal
  ): Promise<boolean> => {
    const backendModelName = MODEL_NAME_MAP[modelType] || modelType;

    setIsGenerating(true);

    try {
      const token = await getToken();
      if (!token) {
        toast.error("Authentication required. Please sign in.");
        return false;
      }

      const response = await axios.post(
        apiUrl("/api/v1/compositions/generate"),
        {
          user_request: userRequest,
          preview_settings: previewSettings,
          media_library: mediaBinItems.map(item => ({
            id: item.id,
            name: item.name,
            mediaType: item.mediaType,
            durationInSeconds: item.durationInSeconds,
            media_width: item.media_width,
            media_height: item.media_height,
            mediaUrlLocal: item.mediaUrlLocal,
            mediaUrlRemote: item.mediaUrlRemote,
          })),
          current_composition: currentComposition,
          preview_frame: null,
          model_name: backendModelName,
          provider: provider,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json"
          },
          signal
        }
      );

      if (response.data.success && response.data.composition_code) {
        try {
          const blueprintJson = JSON.parse(response.data.composition_code);
          const validBlueprint = ensureMinimumTracks(
            Array.isArray(blueprintJson) ? blueprintJson : [],
            4
          );

          onCompositionUpdate(validBlueprint);

          const calculatedDuration = calculateBlueprintDuration(validBlueprint);
          const safeDuration = Math.max(calculatedDuration, 90);
          onDurationUpdate(safeDuration);

          toast.success("AI composition generated successfully!");
          return true;
        } catch (parseError) {
          console.error("AI Generation: JSON parse error:", parseError);
          toast.error("Failed to parse AI response");
          return false;
        }
      } else {
        console.error("AI Generation: API returned error:", response.data.error_message);
        toast.error(response.data.error_message || "Failed to generate composition");
        return false;
      }
    } catch (error) {
      console.error("AI Generation: Network error:", error);
      toast.error("Failed to connect to AI service");
      return false;
    } finally {
      setIsGenerating(false);
    }
  }, [currentComposition, previewSettings, getToken, onCompositionUpdate, onDurationUpdate]);

  const addGeneratedImage = useCallback((item: MediaBinItem) => {
    onMediaBinAdd(item);
  }, [onMediaBinAdd]);

  return [
    { isGenerating },
    { generateComposition, addGeneratedImage }
  ];
}
