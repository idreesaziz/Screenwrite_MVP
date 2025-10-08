/**
 * Test file for string element parser
 * Run with: npx tsx app/video-compositions/test-string-parser.ts
 */

import { parseStringElement, convertStringElementsToFlat } from './stringElementParser';

console.log('=== STRING ELEMENT PARSER TESTS ===\n');

// Test 1: Simple element with parent:root (implicit root system)
console.log('Test 1: Simple element with parent:root');
try {
  const result = parseStringElement('div;id:container;parent:root;backgroundColor:#000;width:100%;height:100%');
  console.log('✅ Result:', JSON.stringify(result, null, 2));
} catch (error) {
  console.log('❌ Error:', error);
}

// Test 2: Element with multiple props
console.log('\nTest 2: Element with multiple props');
try {
  const result = parseStringElement('div;id:box1;parent:root;width:100px;height:200px;opacity:0.5;display:flex');
  console.log('✅ Result:', JSON.stringify(result, null, 2));
} catch (error) {
  console.log('❌ Error:', error);
}

// Test 3: Element with text
console.log('\nTest 3: Element with text');
try {
  const result = parseStringElement('h1;id:title1;parent:root;text:Hello World;fontSize:48px;color:#fff');
  console.log('✅ Result:', JSON.stringify(result, null, 2));
} catch (error) {
  console.log('❌ Error:', error);
}

// Test 4: Element with boolean props
console.log('\nTest 4: Element with boolean props');
try {
  const result = parseStringElement('Video;id:vid1;parent:root;src:https://example.com/video.mp4;muted:true;volume:0.8');
  console.log('✅ Result:', JSON.stringify(result, null, 2));
} catch (error) {
  console.log('❌ Error:', error);
}

// Test 5: Element with array prop
console.log('\nTest 5: Element with array prop');
try {
  const result = parseStringElement('GradientText;id:grad1;parent:root;text:Colorful;colors:[#ff0000,#00ff00,#0000ff];fontSize:64px');
  console.log('✅ Result:', JSON.stringify(result, null, 2));
} catch (error) {
  console.log('❌ Error:', error);
}

// Test 6: Element with object prop
console.log('\nTest 6: Element with object prop');
try {
  const result = parseStringElement('GlitchText;id:glitch1;parent:root;text:Error;shadowColors:{red:#ff0000,cyan:#00ffff};speed:1.5');
  console.log('✅ Result:', JSON.stringify(result, null, 2));
} catch (error) {
  console.log('❌ Error:', error);
}

// Test 7: Element with simple animation
console.log('\nTest 7: Element with simple animation');
try {
  const result = parseStringElement('div;id:box2;parent:root;opacity:@animate[0,1,2]:[0,1,0];fontSize:48px');
  console.log('✅ Result:', JSON.stringify(result, null, 2));
} catch (error) {
  console.log('❌ Error:', error);
}

// Test 8: Element with string animation (fontSize)
console.log('\nTest 8: Element with string animation (fontSize)');
try {
  const result = parseStringElement('div;id:box3;parent:root;fontSize:@animate[0,1,2]:[16px,48px,16px];color:#fff');
  console.log('✅ Result:', JSON.stringify(result, null, 2));
} catch (error) {
  console.log('❌ Error:', error);
}

// Test 9: Element with color animation
console.log('\nTest 9: Element with color animation');
try {
  const result = parseStringElement('div;id:box4;parent:root;color:@animate[0,1,2]:[#ff0000,#00ff00,#0000ff]');
  console.log('✅ Result:', JSON.stringify(result, null, 2));
} catch (error) {
  console.log('❌ Error:', error);
}

// Test 10: Element with transform animation
console.log('\nTest 10: Element with transform animation');
try {
  const result = parseStringElement('div;id:box5;parent:root;transform:@animate[0,2]:[translateX(0px),translateX(100px)]');
  console.log('✅ Result:', JSON.stringify(result, null, 2));
} catch (error) {
  console.log('❌ Error:', error);
}

// Test 11: Convert multiple string elements (implicit root)
console.log('\nTest 11: Convert multiple string elements with implicit root');
try {
  const stringElements = [
    'div;id:box1;parent:root;width:100px;height:100px;backgroundColor:#f00',
    'h1;id:title1;parent:box1;text:Hello;fontSize:32px;color:#fff'
  ];
  const result = convertStringElementsToFlat(stringElements);
  console.log('✅ Result (should have implicit AbsoluteFill root prepended):', JSON.stringify(result, null, 2));
  console.log('✅ Root element:', result[0].name === 'AbsoluteFill' && result[0].id === 'root' ? 'CORRECT' : 'WRONG');
} catch (error) {
  console.log('❌ Error:', error);
}

// Test 12: Error case - missing id
console.log('\nTest 12: Error case - missing id');
try {
  const result = parseStringElement('div;parent:root;color:#fff');
  console.log('❌ Should have thrown error, got:', result);
} catch (error) {
  console.log('✅ Expected error:', (error as Error).message);
}

// Test 13: Error case - missing parent
console.log('\nTest 13: Error case - missing parent');
try {
  const result = parseStringElement('div;id:box1;color:#fff');
  console.log('❌ Should have thrown error, got:', result);
} catch (error) {
  console.log('✅ Expected error:', (error as Error).message);
}

console.log('\n=== ALL TESTS COMPLETE ===');
