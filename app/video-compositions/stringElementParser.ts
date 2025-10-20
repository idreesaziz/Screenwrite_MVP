import type { FlatElement, AnimatedProperty } from "./BlueprintTypes";

/**
 * Parse a single string element into a FlatElement object
 * 
 * Format: "ComponentName;id:value;parent:value;prop:value;..."
 * Animation syntax: "prop:@animate[0,1,2]:[value1,value2,value3]"
 * 
 * Examples:
 * - "AbsoluteFill;id:root;parent:null;backgroundColor:#000"
 * - "Video;id:vid1;parent:root;src:https://example.com/video.mp4;volume:0.8"
 * - "div;id:box1;parent:root;opacity:@animate[0,1,2]:[0,1,0];fontSize:48px"
 */
export function parseStringElement(elementString: string): FlatElement {
  const parts = elementString.split(';');
  
  if (parts.length === 0) {
    throw new Error('Invalid element string: empty string');
  }
  
  // First part is the component name
  const name = parts[0].trim();
  
  if (!name) {
    throw new Error('Invalid element string: missing component name');
  }
  
  const element: FlatElement = {
    id: '',
    name,
    parentId: null,
    props: {}
  };
  
  // Parse the rest as property:value pairs
  for (let i = 1; i < parts.length; i++) {
    const part = parts[i].trim();
    
    if (!part) continue; // Skip empty parts
    
    const colonIndex = part.indexOf(':');
    
    if (colonIndex === -1) {
      console.warn(`Invalid property format (missing colon): "${part}" in element "${name}"`);
      continue;
    }
    
    const propName = part.substring(0, colonIndex).trim();
    const propValue = part.substring(colonIndex + 1).trim();
    
    if (!propName) {
      console.warn(`Invalid property format (empty name): "${part}" in element "${name}"`);
      continue;
    }
    
    // Handle special properties
    if (propName === 'id') {
      element.id = propValue;
      continue;
    }
    
    if (propName === 'parent') {
      // Auto-fix: treat null, "null", or "root" as root reference
      if (propValue === 'null' || propValue === 'root') {
        element.parentId = 'root';
      } else {
        element.parentId = propValue;
      }
      continue;
    }
    
    // For 'text' property, store both in element.text AND props.text
    // This allows it to work as both a child (for h1, p, etc.) and as a prop (for SplitText, etc.)
    if (propName === 'text') {
      element.text = propValue;
      element.props!.text = propValue; // Also store as prop for components that need it
      continue;
    }
    
    // Parse and store the property value
    element.props![propName] = parsePropertyValue(propValue, propName);
  }
  
  // Validate required fields
  if (!element.id) {
    throw new Error(`Missing required "id" property in element "${name}"`);
  }
  
  // Auto-fix: If parent wasn't specified, default to 'root'
  if (!parts.some(p => p.trim().startsWith('parent:'))) {
    element.parentId = 'root';
  }
  
  return element;
}

/**
 * Parse a property value, detecting animations, arrays, objects, booleans, numbers, and strings
 */
function parsePropertyValue(value: string, propName: string): AnimatedProperty<any> {
  // Check for animation syntax: @animate[timestamps]:[values]
  if (value.startsWith('@animate[')) {
    return parseAnimatedProperty(value, propName);
  }
  
  // Check for array syntax: [item1,item2,item3]
  if (value.startsWith('[') && value.endsWith(']')) {
    return parseArrayValue(value);
  }
  
  // Check for object syntax: {key1:value1,key2:value2}
  if (value.startsWith('{') && value.endsWith('}')) {
    return parseObjectValue(value);
  }
  
  // Check for boolean
  if (value === 'true') return true;
  if (value === 'false') return false;
  
  // Check for number (including decimals and negatives)
  if (/^-?\d+\.?\d*$/.test(value)) {
    return parseFloat(value);
  }
  
  // Everything else is a string
  return value;
}

/**
 * Parse animation syntax: @animate[0,1,2]:[value1,value2,value3]
 */
function parseAnimatedProperty(value: string, propName: string): AnimatedProperty<any> {
  // Extract timestamps and values
  const match = value.match(/^@animate\[(.*?)\]:\[(.*?)\]$/);
  
  if (!match) {
    throw new Error(`Invalid animation syntax for property "${propName}": ${value}`);
  }
  
  const timestampsStr = match[1];
  const valuesStr = match[2];
  
  // Parse timestamps (must be numbers)
  const timestamps = timestampsStr.split(',').map(t => {
    const num = parseFloat(t.trim());
    if (isNaN(num)) {
      throw new Error(`Invalid timestamp "${t}" in animation for property "${propName}"`);
    }
    return num;
  });
  
  // Parse values (can be any type)
  const values = valuesStr.split(',').map(v => parseSimpleValue(v.trim()));
  
  // Validate lengths match
  if (timestamps.length !== values.length) {
    throw new Error(
      `Animation timestamp/value count mismatch for property "${propName}": ` +
      `${timestamps.length} timestamps, ${values.length} values`
    );
  }
  
  // Validate at least 2 keyframes
  if (timestamps.length < 2) {
    throw new Error(`Animation for property "${propName}" must have at least 2 keyframes`);
  }
  
  return {
    timestamps,
    values
  };
}

/**
 * Parse array syntax: [item1,item2,item3]
 */
function parseArrayValue(value: string): any[] {
  const content = value.slice(1, -1).trim(); // Remove [ and ]
  
  if (!content) {
    return []; // Empty array
  }
  
  return content.split(',').map(item => parseSimpleValue(item.trim()));
}

/**
 * Parse object syntax: {key1:value1,key2:value2}
 */
function parseObjectValue(value: string): Record<string, any> {
  const content = value.slice(1, -1).trim(); // Remove { and }
  
  if (!content) {
    return {}; // Empty object
  }
  
  const obj: Record<string, any> = {};
  
  // Split by comma, but be careful with nested structures
  const pairs = content.split(',');
  
  for (const pair of pairs) {
    const colonIndex = pair.indexOf(':');
    
    if (colonIndex === -1) {
      console.warn(`Invalid object property format (missing colon): "${pair}"`);
      continue;
    }
    
    const key = pair.substring(0, colonIndex).trim();
    const val = pair.substring(colonIndex + 1).trim();
    
    if (!key) {
      console.warn(`Invalid object property format (empty key): "${pair}"`);
      continue;
    }
    
    obj[key] = parseSimpleValue(val);
  }
  
  return obj;
}

/**
 * Parse a simple value (no arrays or objects, used within arrays/objects/animations)
 */
function parseSimpleValue(value: string): any {
  // Boolean
  if (value === 'true') return true;
  if (value === 'false') return false;
  
  // Number
  if (/^-?\d+\.?\d*$/.test(value)) {
    return parseFloat(value);
  }
  
  // String (return as-is)
  return value;
}

/**
 * Convert an array of string elements to FlatElement array
 * Automatically adds implicit AbsoluteFill root element
 */
export function convertStringElementsToFlat(stringElements: string[]): FlatElement[] {
  const parsedElements = stringElements.map((elementString, index) => {
    try {
      return parseStringElement(elementString);
    } catch (error) {
      throw new Error(
        `Failed to parse element at index ${index}: ${error instanceof Error ? error.message : String(error)}\n` +
        `Element string: "${elementString}"`
      );
    }
  });
  
  // Automatically prepend implicit AbsoluteFill root element
  const implicitRoot: FlatElement = {
    id: 'root',
    name: 'AbsoluteFill',
    parentId: null,
    props: {}
  };
  
  return [implicitRoot, ...parsedElements];
}

/**
 * Type guard to check if an element container has string elements
 */
export function hasStringElements(container: any): container is { elements: string[] } {
  return (
    container &&
    typeof container === 'object' &&
    'elements' in container &&
    Array.isArray(container.elements) &&
    container.elements.length > 0 &&
    typeof container.elements[0] === 'string'
  );
}
