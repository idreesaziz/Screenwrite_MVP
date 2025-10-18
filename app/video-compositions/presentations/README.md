# Custom Transition Presentations

This directory contains custom transition presentations for the Remotion-based video composition system.

## Available Custom Transitions

### 1. Zoom Transitions (`zoom.tsx`)

**zoom-in**: Scale-based transition that starts small (0.5x) and grows to normal size (1x)
- Creates a dramatic entrance effect
- Smooth scale interpolation
- Only affects entering slide

**zoom-out**: Scale-based transition that starts large (1.5x) and shrinks to normal size (1x)
- Creates a reveal effect
- Smooth scale interpolation
- Only affects entering slide

**Blueprint Usage:**
```json
{
  "transitionToNext": {
    "type": "zoom-in",
    "durationInSeconds": 1.0
  }
}
```

### 2. Blur Transition (`blur.tsx`)

**blur**: Blur-based crossfade with opacity
- Exiting slide: blurs from 0 to 20px while fading out
- Entering slide: blurs from 20px to 0 while fading in
- Creates a dreamy, soft transition effect
- Affects both entering and exiting slides

**Blueprint Usage:**
```json
{
  "transitionToNext": {
    "type": "blur",
    "durationInSeconds": 0.8
  }
}
```

### 3. Glitch Transition (`glitch.tsx`)

**glitch**: Digital glitch effect with RGB distortion
- Random horizontal/vertical offsets
- Hue rotation for color distortion
- Scale variation for visual chaos
- Contrast and saturation boost
- Peak intensity at 30% and 70% of transition
- Only affects entering slide

**Blueprint Usage:**
```json
{
  "transitionToNext": {
    "type": "glitch",
    "durationInSeconds": 0.6
  }
}
```

## Technical Implementation

All custom presentations follow the Remotion custom presentation pattern:

```typescript
export const customPresentation = (
  props: CustomProps
): TransitionPresentation<CustomProps> => {
  return {
    component: CustomComponent,
    props,
  };
};
```

Each presentation component receives:
- `children`: The slide content to render
- `presentationDirection`: Either "entering" or "exiting"
- `presentationProgress`: Number from 0 to 1
- `passedProps`: Custom props (width, height, etc.)

## Adding New Custom Transitions

1. Create a new file in this directory (e.g., `rotate.tsx`)
2. Implement the presentation function and component
3. Export the presentation function
4. Add the transition type to `BlueprintTypes.ts`
5. Import and register in `BlueprintComposition.tsx` in `getTransitionPresentation()`
6. Test in `EmptyComposition.ts`

## See Also

- [Remotion Custom Presentations Docs](https://www.remotion.dev/docs/transitions/presentations/custom)
- [Remotion Built-in Presentations](https://github.com/remotion-dev/remotion/tree/main/packages/transitions/src/presentations)
