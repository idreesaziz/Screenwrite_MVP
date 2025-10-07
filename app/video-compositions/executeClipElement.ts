import React from "react";
import type { 
  BlueprintExecutionContext, 
  ElementObject, 
  AnimatedProperty, 
  ElementContainer 
} from "./BlueprintTypes";
import { 
  getComponentSchema, 
  getComponent, 
  shouldBeComponentProp, 
  shouldBeStyleProp 
} from "./componentRegistry";
import { convertFlatToNested } from "./flatElementConverter";
import { 
  convertStringElementsToFlat, 
  hasStringElements
} from "./stringElementParser";

/**
 * Parse a hex color to RGB components
 */
function parseHexColor(hex: string): [number, number, number] {
  const cleaned = hex.replace('#', '');
  const r = parseInt(cleaned.substring(0, 2), 16);
  const g = parseInt(cleaned.substring(2, 4), 16);
  const b = parseInt(cleaned.substring(4, 6), 16);
  return [r, g, b];
}

/**
 * Convert RGB components to hex color
 */
function rgbToHex(r: number, g: number, b: number): string {
  const toHex = (n: number) => {
    const clamped = Math.round(Math.max(0, Math.min(255, n)));
    return clamped.toString(16).padStart(2, '0');
  };
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

/**
 * Extract all numbers with their units from a CSS string
 * Returns array of {value, unit, startIndex, endIndex}
 */
function extractNumbersWithUnits(str: string): Array<{value: number, unit: string, startIndex: number, endIndex: number}> {
  // Match numbers (including decimals and negatives) followed by optional units
  const regex = /(-?\d+\.?\d*)(px|%|em|rem|vw|vh|vmin|vmax|deg|rad|turn|s|ms)?/g;
  const matches: Array<{value: number, unit: string, startIndex: number, endIndex: number}> = [];
  
  let match;
  while ((match = regex.exec(str)) !== null) {
    // Skip empty matches or matches that are just the unit
    if (match[1] && match[1].length > 0) {
      matches.push({
        value: parseFloat(match[1]),
        unit: match[2] || '',
        startIndex: match.index,
        endIndex: match.index + match[0].length
      });
    }
  }
  
  return matches;
}

/**
 * Reconstruct a string by replacing numbers at specific positions
 */
function reconstructString(original: string, interpolatedMatches: Array<{value: number, unit: string, startIndex: number, endIndex: number}>): string {
  let result = '';
  let lastIndex = 0;
  
  for (const match of interpolatedMatches) {
    // Add the part before this number
    result += original.substring(lastIndex, match.startIndex);
    // Add the interpolated number with its unit
    result += match.value.toString() + match.unit;
    lastIndex = match.endIndex;
  }
  
  // Add any remaining part of the string
  result += original.substring(lastIndex);
  
  return result;
}

/**
 * Resolve an animated property at render time using context.interp
 * Supports:
 * - Numbers (unitless)
 * - Strings with number+unit (e.g., "100px", "50%")
 * - Hex colors (e.g., "#ff0000")
 * - Complex CSS strings (e.g., "translateX(100px) scale(1.5)", "blur(5px) brightness(150%)")
 * All animations use 'inOut' easing (hardcoded)
 */
function resolveAnimatedProperty<T>(
  prop: AnimatedProperty<T>,
  context: BlueprintExecutionContext
): T {
  // Check if it's an animated property object
  if (
    typeof prop === 'object' && 
    prop !== null && 
    'timestamps' in prop && 
    'values' in prop &&
    Array.isArray((prop as any).timestamps) &&
    Array.isArray((prop as any).values)
  ) {
    const animatedProp = prop as { timestamps: number[]; values: T[] };
    const { timestamps, values } = animatedProp;
    
    // If all values are numbers, interpolate directly
    if (values.every(v => typeof v === 'number')) {
      return context.interp(timestamps, values as any, 'inOut') as T;
    }
    
    // If all values are strings, handle different string formats
    if (values.every(v => typeof v === 'string')) {
      const stringValues = values as unknown as string[];
      
      // Check if all values are hex colors
      if (stringValues.every(v => /^#[0-9a-fA-F]{6}$/.test(v))) {
        // Interpolate RGB components separately
        const rgbValues = stringValues.map(parseHexColor);
        const r = context.interp(timestamps, rgbValues.map(rgb => rgb[0]), 'inOut');
        const g = context.interp(timestamps, rgbValues.map(rgb => rgb[1]), 'inOut');
        const b = context.interp(timestamps, rgbValues.map(rgb => rgb[2]), 'inOut');
        return rgbToHex(r, g, b) as T;
      }
      
      // For other strings, extract all numbers with units and interpolate each
      const firstValue = stringValues[0];
      const parsedValues = stringValues.map(extractNumbersWithUnits);
      
      // Verify all values have the same structure (same number of numeric values)
      const numCount = parsedValues[0].length;
      if (!parsedValues.every(p => p.length === numCount)) {
        console.warn('Animated property values have inconsistent structure:', stringValues);
        return firstValue as T;
      }
      
      // Interpolate each numeric component
      const interpolatedMatches = parsedValues[0].map((match, index) => {
        const numericValues = parsedValues.map(p => p[index].value);
        const interpolatedValue = context.interp(timestamps, numericValues, 'inOut');
        
        return {
          value: interpolatedValue,
          unit: match.unit,
          startIndex: match.startIndex,
          endIndex: match.endIndex
        };
      });
      
      // Reconstruct the string with interpolated values
      return reconstructString(firstValue, interpolatedMatches) as T;
    }
    
    // Fallback: return first value if types are mixed or unsupported
    console.warn('Unsupported animated property type:', values);
    return values[0];
  }
  
  // Return constant value as-is
  return prop as T;
}

/**
 * Render an ElementObject into a React element tree
 * Recursively handles children and separates props into component props and style props
 */
export function renderElementObject(
  element: ElementObject,
  context: BlueprintExecutionContext
): React.ReactElement {
  try {
    const schema = getComponentSchema(element.name);
    const Component = getComponent(element.name);
    
    const componentProps: Record<string, any> = {};
    const styleProps: Record<string, any> = {};
    
    // Process each prop
    for (const [key, value] of Object.entries(element.props || {})) {
      // SPECIAL CASE: Video/Audio startFrom/endAt are NOT composition timestamps
      // They are frame numbers within the source video file - pass through as-is
      const isMediaTimingProp = 
        (element.name === 'Video' || element.name === 'Audio' || element.name === 'OffthreadVideo') && 
        (key === 'startFrom' || key === 'endAt');
      
      const resolvedValue = isMediaTimingProp 
        ? value  // Pass through as-is for media timing props
        : resolveAnimatedProperty(value, context);
      
      // Determine if this prop goes to component or style
      if (shouldBeComponentProp(key, schema)) {
        componentProps[key] = resolvedValue;
      } else if (shouldBeStyleProp(key, schema)) {
        styleProps[key] = resolvedValue;
      }
    }
    
    // Add style object if there are style props
    if (Object.keys(styleProps).length > 0) {
      componentProps.style = styleProps;
    }
    
    // Recursively render children
    const children = element.children?.map((child, index) => {
      // Handle string children (text content)
      if (typeof child === 'string') {
        return child;
      }
      // Handle ElementObject children (nested elements)
      return renderElementObject(child, context);
    }) || [];
    
    return React.createElement(Component, componentProps, ...children);
  } catch (error) {
    console.error("Error rendering element:", element.name, error);
    
    // Return error display component
    return React.createElement(
      'div',
      {
        style: {
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          backgroundColor: '#1a1a1a',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#ff6b6b',
          fontSize: '16px',
          fontFamily: 'Arial, sans-serif',
          textAlign: 'center' as const,
          padding: '20px',
          zIndex: 1000,
        }
      },
      React.createElement(
        'div',
        {},
        React.createElement('p', {}, '⚠️ Error rendering element: ' + element.name),
        React.createElement(
          'p', 
          { style: { fontSize: '12px', opacity: 0.8, marginTop: '10px' } },
          error instanceof Error ? error.message : 'Unknown error'
        )
      )
    );
  }
}

/**
 * Main entry point for executing/rendering a clip element
 * Converts string element structure to nested tree and renders it
 * Automatically wraps non-AbsoluteFill root elements in AbsoluteFill
 */
export function executeClipElement(
  element: ElementContainer,
  context: BlueprintExecutionContext
): React.ReactElement {
  // Only accept string format - convert to flat elements first
  if (!hasStringElements(element)) {
    throw new Error('Invalid element container: must have string[] elements in format "ComponentName;id:value;parent:value;prop:value"');
  }
  
  // Parse string elements to flat element objects
  const flatElements = convertStringElementsToFlat(element.elements);
  const flatElementContainer = { elements: flatElements };
  
  // Convert flat element structure to nested tree
  const nestedElement = convertFlatToNested(flatElementContainer);
  
  // If root element is not AbsoluteFill, wrap it automatically
  if (nestedElement.name !== 'AbsoluteFill') {
    const wrappedElement: ElementObject = {
      name: 'AbsoluteFill',
      props: {},
      children: [nestedElement]
    };
    return renderElementObject(wrappedElement, context);
  }
  
  return renderElementObject(nestedElement, context);
}

/**
 * Calculate total composition duration from blueprint
 * Works with intelligent track system that respects actual timing and transitions
 */
export function calculateBlueprintDuration(blueprint: import('./BlueprintTypes').CompositionBlueprint): number {
  let maxDuration = 0;

  // Find the latest end time across all tracks and clips, accounting for transitions
  for (const track of blueprint) {
    if (!track.clips || track.clips.length === 0) continue;
    
    for (const clip of track.clips) {
      let clipEndTime = clip.endTimeInSeconds;
      
      // Account for orphaned transitions that extend the clip
      if (clip.transitionToNext && clip.transitionToNext.durationInSeconds) {
        // Only extend if this is an orphaned transition (no adjacent clip)
        const isOrphanedTransition = true; // Assume orphaned for duration calculation safety
        if (isOrphanedTransition) {
          clipEndTime += clip.transitionToNext.durationInSeconds * 0.5; // Partial extension for safety
        }
      }
      
      if (clipEndTime > maxDuration) {
        maxDuration = clipEndTime;
      }
    }
  }

  // Convert seconds to frames (30 FPS) with minimum duration
  const durationInFrames = Math.ceil(maxDuration * 30);
  return Math.max(durationInFrames, 30); // Minimum 1 second
}
