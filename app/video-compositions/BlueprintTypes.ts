// Blueprint-based composition system interfaces
// Updated to match proper Remotion TransitionSeries implementation

// Available transition types - direction encoded in name for simplicity
export type TransitionType = 
  // Basic transitions (no direction)
  | 'fade'
  | 'clock-wipe'
  | 'iris'
  // Slide transitions (4 directions)
  | 'slide-left'
  | 'slide-right'
  | 'slide-top'
  | 'slide-bottom'
  // Wipe transitions (8 directions)
  | 'wipe-left'
  | 'wipe-right'
  | 'wipe-top'
  | 'wipe-bottom'
  | 'wipe-top-left'
  | 'wipe-top-right'
  | 'wipe-bottom-left'
  | 'wipe-bottom-right'
  // Flip transitions (4 directions)
  | 'flip-left'
  | 'flip-right'
  | 'flip-top'
  | 'flip-bottom';

// Simplified transition config - only 2 parameters
export interface TransitionConfig {
  type: TransitionType;           // Direction encoded in name
  durationInSeconds: number;      // Duration of transition
}

// Simplified transition config - only type and duration
export interface TransitionConfig {
  type: TransitionType;
  durationInSeconds: number;
}

// Animated property: can be constant or timeline-based
export type AnimatedProperty<T> = T | {
  timestamps: number[];  // GLOBAL composition timestamps in seconds (NOT clip-relative)
  values: T[];          // Corresponding values at each timestamp
  // easing is ALWAYS 'inOut' - hardcoded in renderer
};

// Flat element structure from backend - uses parentId references
export interface FlatElement {
  id: string;  // Unique identifier
  name: string;  // Component name: "div", "Video", "Img", "AbsoluteFill", etc.
  parentId: string | null;  // ID of parent element, null for root
  props?: Record<string, AnimatedProperty<any>>;  // All props in flat structure
  text?: string;  // Text content for this element (if any)
}

// Container for flat element list (internal use only after parsing)
export interface FlatElementContainer {
  elements: FlatElement[];
}

// Container for string element list (required format from AI)
export interface StringElementContainer {
  elements: string[];
}

// Only string format is accepted
export type ElementContainer = StringElementContainer;

// Nested element structure for rendering - built from flat elements
export interface ElementObject {
  name: string;  // Component name: "div", "Video", "Img", "AbsoluteFill", etc.
  props?: Record<string, AnimatedProperty<any>>;  // All props in flat structure
  children?: (ElementObject | string)[];  // Recursive children: can be nested elements OR text strings
}

// Component schema - defines how to handle props for each component type
export interface ComponentSchema {
  type: 'html' | 'component';
  componentProps?: string[] | '*';  // Props passed directly to component, '*' means all props
  styleProps: '*' | string[];  // '*' means all other props go to style, [] means no style support
}

export interface Clip {
  id: string;
  startTimeInSeconds: number;
  endTimeInSeconds: number;
  element: ElementContainer; // Supports both string[] and FlatElement[] formats
  transitionToNext?: TransitionConfig;
  transitionFromPrevious?: TransitionConfig;
}

export interface Track {
  clips: Clip[];
}

export type CompositionBlueprint = Track[];

// Helper types for rendering modes
export type RenderingMode = 'blueprint' | 'string';

export interface BlueprintExecutionContext {
  // Helper functions available to clip code
  interp: (timestamps: number[], values: number[], easing?: 'linear' | 'in' | 'out' | 'inOut') => number;
  inSeconds: (seconds: number) => number;
  // Sequence timing context for proper interp calculations
  sequenceStartTime: number; // Start time of the current sequence in seconds
  // Add more helper functions as needed
}
