import type { CompositionBlueprint } from './BlueprintTypes';

/**
 * Empty composition blueprint with 3 tracks ready for content
 */
export const emptyCompositionBlueprint: CompositionBlueprint = [
  // Track 1
  {
    clips: []
  },
  // Track 2
  {
    clips: []
  },
  // Track 3
  {
    clips: []
  }
];

/**
 * Ensure composition has minimum required tracks
 * Automatically expands to accommodate content without losing existing data
 */
export function ensureMinimumTracks(blueprint: CompositionBlueprint, minTracks: number = 4): CompositionBlueprint {
  const result = [...blueprint];
  
  // Add empty tracks if we don't have enough
  while (result.length < minTracks) {
    result.push({ clips: [] });
  }
  
  return result;
}
