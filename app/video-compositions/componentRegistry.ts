/**
 * Component Registry for Element Rendering
 * 
 * Defines how props should be handled for each component type:
 * - Component props: passed directly to the component
 * - Style props: grouped into a style object
 */

import type { ComponentSchema } from './BlueprintTypes';
import * as Remotion from 'remotion';
import React from 'react';
import { SplitText, BlurText, TypewriterText } from './text-animations';

export const COMPONENT_REGISTRY: Record<string, ComponentSchema> = {
  // Standard HTML elements - all props go to style
  'div': { type: 'html', styleProps: '*' },
  'span': { type: 'html', styleProps: '*' },
  'h1': { type: 'html', styleProps: '*' },
  'h2': { type: 'html', styleProps: '*' },
  'h3': { type: 'html', styleProps: '*' },
  'h4': { type: 'html', styleProps: '*' },
  'h5': { type: 'html', styleProps: '*' },
  'h6': { type: 'html', styleProps: '*' },
  'p': { type: 'html', styleProps: '*' },
  'button': { type: 'html', styleProps: '*' },
  'img': { type: 'html', styleProps: '*' },
  'a': { type: 'html', styleProps: '*' },
  'section': { type: 'html', styleProps: '*' },
  'article': { type: 'html', styleProps: '*' },
  'header': { type: 'html', styleProps: '*' },
  'footer': { type: 'html', styleProps: '*' },
  'nav': { type: 'html', styleProps: '*' },
  'main': { type: 'html', styleProps: '*' },
  'aside': { type: 'html', styleProps: '*' },
  
  // Remotion components - define specific component props
  'AbsoluteFill': { 
    type: 'component',
    componentProps: [],
    styleProps: '*'
  },
  'Video': { 
    type: 'component',
    componentProps: ['src', 'startFrom', 'endAt', 'volume', 'playbackRate', 'muted', 'loop', 'crossOrigin'],
    styleProps: '*'
  },
  'Audio': {
    type: 'component',
    componentProps: ['src', 'startFrom', 'endAt', 'volume', 'playbackRate', 'muted', 'loop'],
    styleProps: []  // Audio has no visual styles
  },
  'Img': { 
    type: 'component',
    componentProps: ['src', 'alt', 'crossOrigin'],
    styleProps: '*'
  },
  'Sequence': {
    type: 'component',
    componentProps: ['from', 'durationInFrames', 'layout', 'name'],
    styleProps: '*'
  },
  'Series': {
    type: 'component',
    componentProps: ['layout'],
    styleProps: []
  },
  'OffthreadVideo': {
    type: 'component',
    componentProps: ['src', 'startFrom', 'endAt', 'volume', 'playbackRate', 'muted', 'loop', 'transparent'],
    styleProps: '*'
  },
  'IFrame': {
    type: 'component',
    componentProps: ['src', 'allow', 'allowFullScreen', 'sandbox'],
    styleProps: '*'
  },
  
  // Text Animation Components
  'SplitText': {
    type: 'component',
    componentProps: ['text', 'animateBy', 'direction', 'delay', 'duration'],
    styleProps: '*'
  },
  'BlurText': {
    type: 'component',
    componentProps: ['text', 'animateBy', 'direction', 'delay', 'duration'],
    styleProps: '*'
  },
  'TypewriterText': {
    type: 'component',
    componentProps: ['text', 'typingSpeed', 'initialDelay', 'pauseDuration', 'deletingSpeed', 'loop', 'showCursor', 'cursorCharacter', 'cursorBlinkSpeed'],
    styleProps: '*'
  },
};

/**
 * Get component schema for a given component name
 * Returns default schema for unknown components
 */
export function getComponentSchema(componentName: string): ComponentSchema {
  return COMPONENT_REGISTRY[componentName] || {
    // Default: assume custom component, all props are component props (safe default)
    type: 'component',
    componentProps: '*',  // Special value meaning "pass everything as component props"
    styleProps: []
  };
}

/**
 * Get the actual component reference for rendering
 */
export function getComponent(componentName: string): any {
  // Check text animation components first
  if (componentName === 'SplitText') {
    return SplitText;
  }
  if (componentName === 'BlurText') {
    return BlurText;
  }
  if (componentName === 'TypewriterText') {
    return TypewriterText;
  }
  
  // Check Remotion namespace
  if (componentName in Remotion) {
    return (Remotion as any)[componentName];
  }
  
  // Check React namespace
  if (componentName in React) {
    return (React as any)[componentName];
  }
  
  // Assume it's an HTML element string
  return componentName;
}

/**
 * Determine if a prop should be passed as a component prop
 */
export function shouldBeComponentProp(propName: string, schema: ComponentSchema): boolean {
  if (!schema.componentProps) {
    return false;
  }
  
  if (schema.componentProps === '*') {
    return true;
  }
  
  return schema.componentProps.includes(propName);
}

/**
 * Determine if a prop should be passed as a style prop
 */
export function shouldBeStyleProp(propName: string, schema: ComponentSchema): boolean {
  // Special case: 'children' is never a style prop
  if (propName === 'children') {
    return false;
  }
  
  if (schema.styleProps === '*') {
    // If componentProps is also '*', then nothing goes to style
    if (schema.componentProps === '*') {
      return false;
    }
    // Otherwise, any prop not in componentProps goes to style
    return !shouldBeComponentProp(propName, schema);
  }
  
  return schema.styleProps.includes(propName);
}
