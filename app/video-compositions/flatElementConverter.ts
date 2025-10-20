/**
 * Utility to convert flat element list (with parentId references) to nested tree structure
 */

import type { FlatElement, FlatElementContainer, ElementObject } from "./BlueprintTypes";

/**
 * Convert flat element list to nested tree structure
 * 
 * @param flatContainer - Container with flat elements array
 * @returns Root ElementObject with nested children
 */
export function convertFlatToNested(flatContainer: FlatElementContainer): ElementObject {
  const { elements } = flatContainer;
  
  if (!elements || elements.length === 0) {
    throw new Error('No elements in flat container');
  }
  
  // Create a map of elements by ID for quick lookup
  const elementMap = new Map<string, FlatElement>();
  for (const element of elements) {
    elementMap.set(element.id, element);
  }
  
  // Create a map to store converted nested elements
  const convertedMap = new Map<string, ElementObject>();
  
  // Helper function to convert a single flat element to nested format
  function convertElement(flatElement: FlatElement): ElementObject {
    // Check if already converted (memoization)
    if (convertedMap.has(flatElement.id)) {
      return convertedMap.get(flatElement.id)!;
    }
    
    // Create the nested element structure
    const nestedElement: ElementObject = {
      name: flatElement.name,
      props: flatElement.props || {},
      children: []
    };
    
    // Store in map before processing children (prevents infinite recursion)
    convertedMap.set(flatElement.id, nestedElement);
    
    // Find all children (elements that have this element as parent)
    const children: (ElementObject | string)[] = [];
    
    for (const potentialChild of elements) {
      if (potentialChild.parentId === flatElement.id) {
        // If the child has text content, add it as a string child
        if (potentialChild.text) {
          // First add the converted element structure
          children.push(convertElement(potentialChild));
        } else {
          // Regular child element without text
          children.push(convertElement(potentialChild));
        }
      }
    }
    
    // Add text content as a string child if present
    if (flatElement.text) {
      children.push(flatElement.text);
    }
    
    // Only set children if there are any
    if (children.length > 0) {
      nestedElement.children = children;
    }
    
    return nestedElement;
  }
  
  // Find the root element (parentId === null or "null" or "root")
  const rootElement = elements.find(el => 
    el.parentId === null || 
    el.parentId === "null" || 
    el.id === "root"
  );
  
  if (!rootElement) {
    throw new Error('No root element found (expected element with parentId: null)');
  }
  
  // Convert the root and all its descendants
  return convertElement(rootElement);
}


