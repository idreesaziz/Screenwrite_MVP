/**
 * Composition Module
 * 
 * Remotion-based video composition system using blueprints.
 * Renders clips with transitions, text animations, and media.
 */

// Types
export type {
  CompositionBlueprint,
  Track,
  Clip,
  ClipElement,
  TransitionConfig,
  ComponentSchema,
} from './types/BlueprintTypes';

// Composition Components
export { BlueprintComposition } from './core/BlueprintComposition';
export { DynamicVideoPlayer } from './core/DynamicComposition';
export { StandalonePreviewComposition, StandaloneVideoPlayer } from './core/StandalonePreview';

// Utilities
export { emptyCompositionBlueprint, ensureMinimumTracks } from './utils/EmptyComposition';
export { calculateBlueprintDuration, executeClipElement } from './execution/executeClipElement';
export { parseElementString, parsePropsFromString } from './execution/stringElementParser';
export { convertFlatToNested } from './execution/flatElementConverter';
export { COMPONENT_REGISTRY, getRemotionComponent } from './execution/componentRegistry';

// Text Animations
export {
  SplitText,
  BlurText,
  TypewriterText,
  GradientText,
  TrueFocus,
} from './text-animations';
