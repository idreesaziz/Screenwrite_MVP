/**
 * Generate a unique name from a title by adding (2), (3) etc. suffixes if duplicates exist
 * @param title - The desired title/name
 * @param existingItems - Array of existing media items to check against
 * @returns Unique name with suffix if needed
 */
export function generateUniqueName(
  title: string,
  existingItems: Array<{ name: string }>
): string {
  // Start with the base title
  let candidateName = title;
  let suffix = 2;
  
  // Get set of existing names for fast lookup
  const existingNames = new Set(existingItems.map(item => item.name));
  
  // Keep incrementing suffix until we find a unique name
  while (existingNames.has(candidateName)) {
    candidateName = `${title} (${suffix})`;
    suffix++;
  }
  
  return candidateName;
}

/**
 * Clean a filename to make it a nice title
 * - Remove file extension
 * - Replace underscores and hyphens with spaces
 * - Capitalize first letter of each word
 * @param filename - The original filename
 * @returns Cleaned title
 */
export function cleanFilenameToTitle(filename: string): string {
  // Remove extension
  const withoutExt = filename.replace(/\.[^/.]+$/, '');
  
  // Replace underscores and hyphens with spaces
  const withSpaces = withoutExt.replace(/[_-]/g, ' ');
  
  // Capitalize first letter of each word
  const capitalized = withSpaces
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
  
  return capitalized;
}
