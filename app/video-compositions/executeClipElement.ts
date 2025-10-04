import React from "react";
import type { BlueprintExecutionContext, ElementObject, AnimatedProperty } from "./BlueprintTypes";
import { 
  getComponentSchema, 
  getComponent, 
  shouldBeComponentProp, 
  shouldBeStyleProp 
} from "./componentRegistry";

/**
 * Resolve an animated property at render time using context.interp
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
    
    // Use context.interp with hardcoded 'inOut' easing
    // context.interp handles conversion from global timestamps to frame-relative
    return context.interp(
      animatedProp.timestamps,
      animatedProp.values as any,
      'inOut'
    ) as T;
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
 * Automatically wraps non-AbsoluteFill root elements in AbsoluteFill
 */
export function executeClipElement(
  element: ElementObject,
  context: BlueprintExecutionContext
): React.ReactElement {
  // If root element is not AbsoluteFill, wrap it automatically
  if (element.name !== 'AbsoluteFill') {
    const wrappedElement: ElementObject = {
      name: 'AbsoluteFill',
      props: {},
      children: [element]
    };
    return renderElementObject(wrappedElement, context);
  }
  
  return renderElementObject(element, context);
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
