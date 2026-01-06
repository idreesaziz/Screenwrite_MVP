import type { CompositionBlueprint } from './BlueprintTypes';

/**
 * Empty composition with 3 tracks
 */
export const emptyCompositionBlueprint: CompositionBlueprint = [
  {
    clips: []
  },
  {
    clips: []
  },
  {
    clips: []
  }
];

/**
 * Ensure composition has minimum required tracks
 * Automatically expands to accommodate content without losing existing data
 */
export function ensureMinimumTracks(blueprint: CompositionBlueprint, minTracks: number = 3): CompositionBlueprint {
  const result = [...blueprint];
  
  // Add empty tracks if we don't have enough
  while (result.length < minTracks) {
    result.push({ clips: [] });
  }
  
  return result;
}
