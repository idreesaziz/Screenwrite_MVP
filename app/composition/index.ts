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
} from './BlueprintTypes';

// Composition Components
export { BlueprintComposition } from './BlueprintComposition';
export { DynamicVideoPlayer } from './DynamicComposition';
export { StandalonePreviewComposition, StandaloneVideoPlayer } from './StandalonePreview';

// Utilities
export { emptyCompositionBlueprint, ensureMinimumTracks } from './EmptyComposition';
export { calculateBlueprintDuration, executeClipElement } from './executeClipElement';
export { parseElementString, parsePropsFromString } from './stringElementParser';
export { convertFlatToNested } from './flatElementConverter';
export { COMPONENT_REGISTRY, getRemotionComponent } from './componentRegistry';

// Text Animations
export {
  SplitText,
  BlurText,
  TypewriterText,
  GradientText,
  TrueFocus,
} from './text-animations';
