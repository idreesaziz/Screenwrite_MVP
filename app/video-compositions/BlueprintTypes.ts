// Blueprint-based composition system interfaces
// Updated to match proper Remotion TransitionSeries implementation

// Available transition types from Remotion
export type TransitionType = 
  | 'fade'
  | 'slide'
  | 'wipe' 
  | 'flip'
  | 'clockWipe'
  | 'iris';

// Direction options for slide and flip transitions
export type SlideFlipDirection = 'from-left' | 'from-right' | 'from-top' | 'from-bottom';

// Direction options for wipe transitions (includes diagonals)
export type WipeDirection = 
  | 'from-left'
  | 'from-right' 
  | 'from-top'
  | 'from-bottom'
  | 'from-top-left'
  | 'from-top-right'
  | 'from-bottom-left'
  | 'from-bottom-right';

// Union of all possible directions
export type TransitionDirection = SlideFlipDirection | WipeDirection;

export interface TransitionConfig {
  type: TransitionType;
  durationInSeconds: number;
  direction?: TransitionDirection; // For slide, wipe, flip transitions
  perspective?: number; // For flip transitions (default: 1000)
}

// Animated property: can be constant or timeline-based
export type AnimatedProperty<T> = T | {
  timestamps: number[];  // GLOBAL composition timestamps in seconds (NOT clip-relative)
  values: T[];          // Corresponding values at each timestamp
  // easing is ALWAYS 'inOut' - hardcoded in renderer
};

// Element object structure - unified flat prop structure
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
  element: ElementObject; // Changed from string to ElementObject
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
