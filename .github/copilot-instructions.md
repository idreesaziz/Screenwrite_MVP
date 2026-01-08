# GitHub Copilot Instruction

Before implementing any change—no matter how small—ask me to detail exactly what you're planning to do. Only after I explicitly say "go ahead" (green light), proceed with the edit.

NEVER EVER emojis!!!

## Frontend Project Structure

```
app/
  app.css                 # Global styles
  root.tsx                # App root with providers
  routes.ts               # Route definitions (React Router 7)

  routes/                 # Route components (pages)
    Home.tsx              # Main editor page
    NotFound.tsx          # 404 page
    SignIn.tsx            # Authentication page

  components/
    editor/               # Editor-specific components
      auth/               # AuthProvider, ProtectedRoute
      canvas/             # TransformOverlay (clip manipulation)
      chat/               # ChatBox, ProviderPairingModal, SessionHistory, SettingsModal
      layout/             # LeftPanel, PropertiesPanel
      timeline/           # MediaBin, TimelineView, Scrubber, Transitions, adapters, types
    ui/                   # UI primitives (shadcn/radix)

  composition/            # Remotion video composition system
    index.ts              # Barrel export
    types/                # BlueprintTypes (CompositionBlueprint, Track, Clip, etc.)
    core/                 # BlueprintComposition, DynamicComposition, StandalonePreview
    execution/            # componentRegistry, executeClipElement, stringElementParser, flatElementConverter
    utils/                # EmptyComposition
    presentations/        # Transition effects (blur, clock-wipe, glitch, iris, zoom)
    text-animations/      # Text effects (BlurText, GradientText, SplitText, TrueFocus, TypewriterText)

  hooks/                  # Custom React hooks
    useAuth.ts            # Supabase authentication
    useSession.ts         # Session management (save/load)
    useChatSession.ts     # Chat session state
    useChatMessages.tsx   # Message formatting (returns JSX)
    useChatInput.ts       # Chat input handling
    useChatMediaOperations.ts  # Media operations from chat
    useChatWorkflow.ts    # Chat workflow state
    useAIGeneration.ts    # AI composition generation
    useCompositionEditor.ts    # Composition editing operations
    usePlayerControls.ts  # Video player controls
    useMediaBin.ts        # Media library management
    useUndoRedo.ts        # Undo/redo state

  lib/                    # Utilities and API
    api.ts                # Backend URL, composition generation
    authApi.ts            # Authenticated requests
    sessionApi.ts         # Session persistence
    supabase.ts           # Supabase client
    transformUtils.ts     # Clip transform calculations
    animations.ts         # Remotion animation helpers
    utils.ts              # General utilities (cn)
    uuid.ts               # UUID generation

  types/                  # Shared TypeScript types
    chat.ts               # Chat/agent types
    provider.ts           # Provider type definitions
```

## Stack

- React Router 7 (SSR)
- Vite 7.1.5
- Remotion 4.0.340
- TypeScript
- Tailwind CSS + Radix UI (shadcn)
- Supabase (auth)