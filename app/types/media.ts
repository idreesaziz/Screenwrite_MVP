// MediaBinItem type definition compatible with existing code
export interface MediaBinItem {
  id: string;
  name: string; // Unique name derived from title, used for AI references (e.g., "Beach Video (2)")
  title: string; // Human-readable display name, can be non-unique
  mediaType: "video" | "image" | "audio" | "text" | "element";
  mediaUrlLocal: string | null;
  mediaUrlRemote: string | null;
  gcsUri?: string; // GCS URI (gs://bucket/path) for Vertex AI backend access
  media_width: number;
  media_height: number;
  durationInSeconds: number;
  
  // Upload tracking properties
  uploadProgress: number | null;
  isUploading: boolean;
  
  // Unified upload status for AI analysis
  upload_status: "uploaded" | "not_uploaded" | "pending";
  
  // Gemini file reference for analysis
  gemini_file_id: string | null;
  
  // Optional blueprint-specific properties
  element?: string;
  text: TextProperties | null;
  left_transition_id: string | null;
  right_transition_id: string | null;
}

export interface TextProperties {
  textContent: string;
  fontSize: number;
  fontFamily: string;
  color: string;
  textAlign: "left" | "center" | "right";
  fontWeight: "normal" | "bold";
}
