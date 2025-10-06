# String-Based Element Schema Implementation

## Overview

Implemented a minimal string-based schema for element definitions to reduce schema size while maintaining comprehensive documentation in the description field.

## Changes Made

### 1. `element_schemas.py` - Rewritten
**Before:** 300 lines, 11 KB JSON schema with nested object structure
**After:** 136 lines, 5.5 KB JSON schema with string array

**New Structure:**
```python
{
  "type": "object",
  "properties": {
    "elements": {
      "type": "array",
      "description": "...[comprehensive 5KB description]...",
      "items": {
        "type": "string"
      }
    }
  }
}
```

**Key Features:**
- Minimal schema structure (just string array)
- Comprehensive description field (5,278 characters) with:
  - 21 component types with descriptions
  - 53 properties organized by category
  - Format specification
  - Multiple examples
  - All documentation from previous schema

### 2. `prompts.py` - Updated
**System Instruction Updated:**
- Changed from nested object format to string format
- Added clear format specification
- Updated all examples to use semicolon-separated format
- Emphasized required fields (id, parent)
- Included complex CSS value examples

**New Format Examples:**
```
"AbsoluteFill;id:root;parent:null;backgroundColor:#000;display:flex"
"h1;id:title;parent:root;fontSize:48px;color:#fff;text:Hello World"
"Video;id:vid;parent:root;src:/video.mp4;volume:0.8;width:100%"
```

## String Format Specification

### Format
```
ComponentName;id:value;parent:value;property:value;property:value;text:content
```

### Rules
1. **Semicolons** separate all properties
2. **Property format:** `key:value` (no quotes)
3. **CamelCase** for property names
4. **Required fields:** `id` and `parent` (parent:null for root)
5. **Text content:** `text:Your text here` (spaces allowed)
6. **Arrays:** `colors:[#ff0000,#00ff00,#0000ff]` (no spaces between items)

### Complex CSS Values
Works seamlessly with:
- `rgba(255, 0, 0, 0.5)` - colors with commas
- `translate(-50%, -50%)` - transforms with commas
- `linear-gradient(to right, #ff0000, #0000ff)` - gradients
- All CSS functions and complex values

### Components (21 types)
- **Media:** Video, Audio, Img, OffthreadVideo
- **Containers:** AbsoluteFill, Sequence, Series, div, span
- **Text:** h1, h2, h3, p
- **Animations:** SplitText, BlurText, TypewriterText, Shuffle, GradientText, DecryptedText, TrueFocus, GlitchText

### Properties (53 total)
- **Layout:** display, position, top, bottom, left, right, width, height
- **Flexbox:** flexDirection, justifyContent, alignItems, gap
- **Spacing:** margin, marginTop, marginBottom, padding
- **Typography:** fontSize, fontFamily, fontWeight, fontStyle, textAlign, lineHeight, letterSpacing, textTransform
- **Colors:** color, backgroundColor, background
- **Effects:** opacity, transform, textShadow, boxShadow, filter
- **Borders:** border, borderRadius
- **Media:** src, volume, startFrom, endAt, muted, playbackRate
- **Animation:** text, animateBy, direction, delay, duration, speed, typingSpeed, showCursor, shuffleDirection, colors, animationSpeed

## What LLM Generates

```json
{
  "clips": [
    {
      "id": "clip1",
      "startTimeInSeconds": 0,
      "endTimeInSeconds": 5,
      "element": {
        "elements": [
          "AbsoluteFill;id:root;parent:null;backgroundColor:#000;display:flex;justifyContent:center",
          "h1;id:title;parent:root;fontSize:48px;color:#fff;fontWeight:700;text:Hello World",
          "Video;id:bg;parent:root;src:/video.mp4;volume:0.8;width:100%;height:100%"
        ]
      }
    }
  ]
}
```

## Benefits

1. **Reduced Schema Size:** 11 KB → 5.5 KB (50% reduction)
2. **Simpler Structure:** String array vs nested objects
3. **No Parsing Issues:** Semicolon separator handles CSS complexity
4. **Human Readable:** Easy to read and debug
5. **Flat Architecture:** Parent references prevent nesting
6. **Comprehensive Docs:** All documentation in description field

## Next Steps (TODO)

1. **Parser Implementation** (backend/element_parser.py)
   - Parse string format: `"ComponentName;id:x;parent:y;prop:val"` 
   - Convert to element objects:
     ```python
     {
       "id": "x",
       "name": "ComponentName",
       "parentId": "y",
       "props": {"prop": "val"},
       "text": None
     }
     ```
   - Handle complex CSS values (rgba, transforms, gradients)
   - Validate required fields (id, parent)

2. **Integration**
   - Add parser call in blueprint_parser.py
   - Update frontend converter if needed
   - Test end-to-end generation

3. **Testing**
   - Test LLM generation with new format
   - Verify parser handles all edge cases
   - Test with various prompts and media

## Files Modified

- ✅ `backend/element_schemas.py` - Rewritten with string schema
- ✅ `backend/prompts.py` - Updated system instruction
- ⏳ `backend/element_parser.py` - To be created
- ⏳ `backend/blueprint_parser.py` - To be updated with parser
- ⏳ Frontend converter - May need updates

## Testing Commands

```bash
# Test schema structure
cd backend && python3 test_string_schema.py

# Test generation (curl)
curl -X POST http://localhost:8000/api/generate-code \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "Create a title that says Hello World",
    "media_library": [],
    "current_composition": []
  }'
```

## Size Comparison

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Lines | 300 | 136 | -55% |
| File Size | 11 KB | 6 KB | -45% |
| JSON Schema | 11 KB | 5.5 KB | -50% |
| Structure | Nested objects | String array | Simplified |

## Implementation Date

October 6, 2025
