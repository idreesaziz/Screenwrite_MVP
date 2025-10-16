import type { Clip, CompositionBlueprint } from "../video-compositions/BlueprintTypes";

/**
 * Transform values for a clip
 */
export interface TransformValues {
  translateX: number;  // pixels
  translateY: number;  // pixels
  scaleX: number;      // 1.0 = 100%
  scaleY: number;      // 1.0 = 100%
  rotation: number;    // degrees
}

/**
 * Bounding box for a clip
 */
export interface BoundingBox {
  x: number;      // left position in pixels
  y: number;      // top position in pixels
  width: number;  // width in pixels
  height: number; // height in pixels
}

/**
 * Parsed element properties from element string
 */
interface ElementProps {
  tag: string;
  id?: string;
  parent?: string;
  [key: string]: string | undefined;
}

/**
 * Parse element string into tag and properties
 * Format: "div;id:myId;parent:root;width:100px;height:200px"
 */
export function parseElementString(elementStr: string): ElementProps {
  const parts = elementStr.split(';');
  const tag = parts[0];
  const props: ElementProps = { tag };
  
  for (let i = 1; i < parts.length; i++) {
    const colonIndex = parts[i].indexOf(':');
    if (colonIndex === -1) continue;
    
    const key = parts[i].substring(0, colonIndex);
    const value = parts[i].substring(colonIndex + 1);
    props[key] = value;
  }
  
  return props;
}

/**
 * Parse CSS dimension value (px, %, vw, vh) into pixels
 * Returns null if value is invalid or not provided
 */
export function parseDimension(
  value: string | undefined,
  containerSize: number
): number | null {
  if (!value) return null;
  
  const numValue = parseFloat(value);
  if (isNaN(numValue)) return null;
  
  // Handle pixels: "100px" -> 100
  if (value.includes('px')) {
    return numValue;
  }
  
  // Handle percentage: "50%" -> containerSize * 0.5
  if (value.includes('%')) {
    return (numValue / 100) * containerSize;
  }
  
  // Handle viewport units: "50vw", "50vh"
  if (value.includes('vw') || value.includes('vh')) {
    return (numValue / 100) * containerSize;
  }
  
  // Plain number, assume pixels
  return numValue;
}

/**
 * Parse CSS transform property into transform values
 * Format: "translate(100px, 50px) scale(1.2, 1.5) rotate(45deg)"
 */
export function parseTransform(transformStr: string): TransformValues {
  const defaults: TransformValues = {
    translateX: 0,
    translateY: 0,
    scaleX: 1,
    scaleY: 1,
    rotation: 0,
  };
  
  if (!transformStr) return defaults;
  
  // Parse translate(X, Y)
  const translateMatch = transformStr.match(/translate\s*\(\s*([^,]+)\s*,\s*([^)]+)\s*\)/);
  if (translateMatch) {
    defaults.translateX = parseFloat(translateMatch[1]) || 0;
    defaults.translateY = parseFloat(translateMatch[2]) || 0;
  }
  
  // Parse scale(X, Y) or scale(uniform)
  const scaleMatch = transformStr.match(/scale\s*\(\s*([^,)]+)\s*(?:,\s*([^)]+))?\s*\)/);
  if (scaleMatch) {
    defaults.scaleX = parseFloat(scaleMatch[1]) || 1;
    defaults.scaleY = scaleMatch[2] ? (parseFloat(scaleMatch[2]) || 1) : defaults.scaleX;
  }
  
  // Parse rotate(deg)
  const rotateMatch = transformStr.match(/rotate\s*\(\s*([^)]+)\s*\)/);
  if (rotateMatch) {
    defaults.rotation = parseFloat(rotateMatch[1]) || 0;
  }
  
  return defaults;
}

/**
 * Build CSS transform string from transform values
 * Format: "translate(Xpx, Ypx) scale(scaleX, scaleY) rotate(Rdeg)"
 */
export function buildTransformCSS(values: TransformValues): string {
  return `translate(${values.translateX}px, ${values.translateY}px) scale(${values.scaleX}, ${values.scaleY}) rotate(${values.rotation}deg)`;
}

/**
 * Find content elements (children) of a given parent element
 */
function findChildElements(parentId: string, allElements: string[]): string[] {
  return allElements.filter(el => {
    const props = parseElementString(el);
    return props.parent === parentId;
  });
}

/**
 * Estimate dimensions of text content based on font size
 * More accurate estimation for typical fonts
 */
function estimateTextDimensions(text: string, fontSize: number, fontWeight?: string): { width: number; height: number } {
  // Average character width varies by weight
  const isBold = fontWeight === 'bold' || fontWeight === '700' || fontWeight === '800' || fontWeight === '900';
  const charWidth = fontSize * (isBold ? 0.65 : 0.55); // Bold text is wider
  
  const lines = text.split('\n');
  const maxLineLength = Math.max(...lines.map(line => line.length));
  
  return {
    width: maxLineLength * charWidth,
    height: lines.length * fontSize * 1.3, // Line height is typically 1.2-1.3x font size
  };
}

/**
 * Check if element is just a positioning container (should be ignored for bounds)
 */
function isPositioningContainer(props: ElementProps): boolean {
  const tag = props.tag.toLowerCase();
  const hasFullDimensions = props.width === '100%' || props.height === '100%';
  const isFlexContainer = props.display === 'flex';
  const isDiv = tag === 'div';
  
  // It's a positioning container if it's a div with flex and full dimensions
  return isDiv && isFlexContainer && hasFullDimensions;
}

/**
 * Calculate actual content bounds by analyzing child elements
 * Recursively walks tree and ignores positioning containers
 */
function calculateContentBounds(
  rootElementId: string,
  allElements: string[],
  compositionWidth: number,
  compositionHeight: number
): BoundingBox | null {
  const children = findChildElements(rootElementId, allElements);
  
  if (children.length === 0) {
    return null;
  }
  
  const contentBounds: BoundingBox[] = [];
  
  for (const childStr of children) {
    const props = parseElementString(childStr);
    
    // If this is a positioning container, recurse to its children
    if (isPositioningContainer(props) && props.id) {
      const nestedContent = calculateContentBounds(props.id, allElements, compositionWidth, compositionHeight);
      if (nestedContent) {
        contentBounds.push(nestedContent);
      }
      continue;
    }
    
    // If child has explicit dimensions, use them
    const explicitWidth = parseDimension(props.width, compositionWidth);
    const explicitHeight = parseDimension(props.height, compositionHeight);
    
    if (explicitWidth && explicitHeight && explicitWidth < compositionWidth && explicitHeight < compositionHeight) {
      contentBounds.push({
        x: 0,
        y: 0,
        width: explicitWidth,
        height: explicitHeight,
      });
      continue;
    }
    
    // Try to estimate based on content type and text
    const tag = props.tag.toLowerCase();
    const text = props.text || '';
    const fontSize = parseDimension(props.fontSize, compositionWidth) || 16;
    const fontWeight = props.fontWeight;
    
    if (text && (tag === 'h1' || tag === 'h2' || tag === 'h3' || tag === 'p' || tag === 'span' || tag === 'div')) {
      // Text element - estimate based on text and font size
      const dims = estimateTextDimensions(text, fontSize, fontWeight);
      contentBounds.push({
        x: 0,
        y: 0,
        width: dims.width,
        height: dims.height,
      });
    } else if (props.id) {
      // Element might have children, recurse
      const nestedContent = calculateContentBounds(props.id, allElements, compositionWidth, compositionHeight);
      if (nestedContent) {
        contentBounds.push(nestedContent);
      }
    }
  }
  
  if (contentBounds.length === 0) {
    return null;
  }
  
  // Return the combined bounds of all content
  return getCombinedBounds(contentBounds);
}

/**
 * Calculate bounding box for a clip based on its root elements
 * Analyzes element tree to determine actual content bounds
 * Returns null if the clip has no selectable content (e.g., pure backgrounds)
 */
export function calculateClipBounds(
  clip: Clip,
  compositionWidth: number,
  compositionHeight: number
): BoundingBox | null {
  const elements = clip.element.elements || [];
  const rootElements = elements.filter((el) => el.includes('parent:root'));
  
  if (rootElements.length === 0) {
    return null; // No content to select
  }
  
  const bounds: BoundingBox[] = [];
  
  for (const rootElementStr of rootElements) {
    const props = parseElementString(rootElementStr);
    
    // Get explicit dimensions if provided
    let width = parseDimension(props.width, compositionWidth);
    let height = parseDimension(props.height, compositionHeight);
    
    // Get explicit position
    let x = parseDimension(props.left, compositionWidth) ?? 0;
    let y = parseDimension(props.top, compositionHeight) ?? 0;
    
    // Check if this is a container element (has children)
    const contentBounds = calculateContentBounds(props.id || '', elements, compositionWidth, compositionHeight);
    
    // If element has 100% dimensions
    if ((width === compositionWidth || props.width === '100%') && 
        (height === compositionHeight || props.height === '100%')) {
      
      // If no content found, this is a background element - use full dimensions
      if (!contentBounds) {
        bounds.push({
          x: 0,
          y: 0,
          width: compositionWidth,
          height: compositionHeight,
        });
        // DON'T continue - we still need to apply transforms below!
      } else {
        // Container with flex/grid layout - calculate content position
        const display = props.display || 'block';
        const justifyContent = props.justifyContent || 'flex-start';
        const alignItems = props.alignItems || 'flex-start';
        
        // Calculate content position based on flex properties
        if (display === 'flex') {
          // Horizontal alignment
          if (justifyContent === 'center') {
            x = (compositionWidth - contentBounds.width) / 2;
          } else if (justifyContent === 'flex-end') {
            x = compositionWidth - contentBounds.width;
          }
          
          // Vertical alignment
          if (alignItems === 'center') {
            y = (compositionHeight - contentBounds.height) / 2;
          } else if (alignItems === 'flex-end') {
            y = compositionHeight - contentBounds.height;
          }
        }
        
        // Account for padding
        const paddingBottom = parseDimension(props.paddingBottom, compositionHeight) || 0;
        const paddingTop = parseDimension(props.paddingTop, compositionHeight) || 0;
        const paddingLeft = parseDimension(props.paddingLeft, compositionWidth) || 0;
        const paddingRight = parseDimension(props.paddingRight, compositionWidth) || 0;
        
        // Apply padding based on alignment
        if (alignItems === 'flex-end') {
          // For flex-end, padding pushes content up from bottom
          y -= paddingBottom;
        } else {
          // For flex-start or center, padding pushes content down from top
          y += paddingTop;
        }
        
        x += paddingLeft;
        
        bounds.push({
          x,
          y,
          width: contentBounds.width,
          height: contentBounds.height,
        });
      }
    } else if (width && height) {
      // Element has explicit dimensions - use them
      
      // Handle right/bottom positioning
      if (props.right && !props.left) {
        const right = parseDimension(props.right, compositionWidth) ?? 0;
        x = compositionWidth - right - width;
      }
      if (props.bottom && !props.top) {
        const bottom = parseDimension(props.bottom, compositionHeight) ?? 0;
        y = compositionHeight - bottom - height;
      }
      
      bounds.push({ x, y, width, height });
    } else if (contentBounds) {
      // No explicit dimensions but has content - use content bounds
      bounds.push({
        x: x || compositionWidth * 0.25,
        y: y || compositionHeight * 0.35,
        width: contentBounds.width,
        height: contentBounds.height,
      });
    }
    
    // Apply existing transforms
    if (props.transform) {
      const transform = parseTransform(props.transform);
      const lastBound = bounds[bounds.length - 1];
      if (lastBound) {
        console.log(`📐 calculateClipBounds for "${clip.id}" - Applying transform:`, transform);
        console.log(`   Before: x=${lastBound.x}, y=${lastBound.y}`);
        lastBound.x += transform.translateX;
        lastBound.y += transform.translateY;
        console.log(`   After: x=${lastBound.x}, y=${lastBound.y}`);
      }
    } else {
      console.log(`📐 calculateClipBounds for "${clip.id}" - No transform found in element "${props.id}"`);
    }
  }
  
  if (bounds.length === 0) {
    return null; // No selectable content found
  }
  
  const finalBounds = getCombinedBounds(bounds);
  console.log(`📐 calculateClipBounds for "${clip.id}" - Final bounds:`, finalBounds);
  
  return finalBounds;
}

/**
 * Combine multiple bounding boxes into a single box that encompasses all
 */
function getCombinedBounds(bounds: BoundingBox[]): BoundingBox {
  if (bounds.length === 0) {
    return { x: 0, y: 0, width: 0, height: 0 };
  }
  
  if (bounds.length === 1) {
    return bounds[0];
  }
  
  // Find min/max extents
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  
  for (const box of bounds) {
    minX = Math.min(minX, box.x);
    minY = Math.min(minY, box.y);
    maxX = Math.max(maxX, box.x + box.width);
    maxY = Math.max(maxY, box.y + box.height);
  }
  
  return {
    x: minX,
    y: minY,
    width: maxX - minX,
    height: maxY - minY,
  };
}

/**
 * Update transform on all root elements of a clip
 * Applies the given transform values to the clip's root elements
 */
export function updateClipTransform(
  clip: Clip,
  transform: Partial<TransformValues>
): Clip {
  console.log('🔄 updateClipTransform called for clip:', clip.id);
  console.log('🔄 Transform to apply:', transform);
  
  const elements = clip.element.elements || [];
  console.log('🔄 Total elements in clip:', elements.length);
  
  let rootElementCount = 0;
  
  const updatedElements = elements.map((elementStr, index) => {
    const props = parseElementString(elementStr);
    
    // Only update root elements
    if (props.parent !== 'root') {
      console.log(`  - Element ${index}: "${props.id}" (parent: ${props.parent}) - SKIPPED (not root)`);
      return elementStr;
    }
    
    rootElementCount++;
    console.log(`  - Element ${index}: "${props.id}" (parent: root) - UPDATING`);
    console.log(`    BEFORE: ${elementStr.substring(0, 100)}...`);
    
    // Parse existing transform or use defaults
    const currentTransform = props.transform
      ? parseTransform(props.transform)
      : {
          translateX: 0,
          translateY: 0,
          scaleX: 1,
          scaleY: 1,
          rotation: 0,
        };
    
    console.log('    Current transform:', currentTransform);
    
    // Merge with new transform values
    const newTransform: TransformValues = {
      ...currentTransform,
      ...transform,
    };
    
    console.log('    New transform:', newTransform);
    
    // Build new transform CSS
    const transformCSS = buildTransformCSS(newTransform);
    console.log('    Transform CSS:', transformCSS);
    
    // Rebuild element string with updated transform
    const { tag, ...propsWithoutTag } = props;
    const updatedProps = { ...propsWithoutTag, transform: transformCSS };
    
    const propStrings = Object.entries(updatedProps)
      .filter(([_, value]) => value !== undefined)
      .map(([key, value]) => `${key}:${value}`);
    
    const updatedElementStr = [tag, ...propStrings].join(';');
    console.log(`    AFTER: ${updatedElementStr.substring(0, 100)}...`);
    
    return updatedElementStr;
  });
  
  console.log(`🔄 Updated ${rootElementCount} root elements`);
  
  return {
    ...clip,
    element: {
      ...clip.element,
      elements: updatedElements,
    },
  };
}

/**
 * Get all clips visible at a given frame
 */
export function getVisibleClips(
  blueprint: CompositionBlueprint,
  currentFrame: number,
  fps: number
): Array<{ clip: Clip; trackIndex: number }> {
  const currentTimeInSeconds = currentFrame / fps;
  const visibleClips: Array<{ clip: Clip; trackIndex: number }> = [];
  
  blueprint.forEach((track, trackIndex) => {
    track.clips.forEach((clip) => {
      if (
        currentTimeInSeconds >= clip.startTimeInSeconds &&
        currentTimeInSeconds < clip.endTimeInSeconds
      ) {
        visibleClips.push({ clip, trackIndex });
      }
    });
  });
  
  return visibleClips;
}
