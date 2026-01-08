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

## Backend Project Structure

```
backend/
  main.py                 # FastAPI app entry point
  pyproject.toml          # Python project config (uv)

  api/                    # API route handlers
    agent_router.py       # AI agent endpoints
    analysis_router.py    # Media analysis endpoints
    composition_router.py # Composition generation endpoints
    media_router.py       # Media management endpoints
    session_router.py     # Session persistence endpoints
    stock_router.py       # Stock media search endpoints
    upload_router.py      # File upload endpoints

  business_logic/         # Core business logic
    analyze_media.py      # Media analysis logic
    fetch_media.py        # Stock media fetching
    generate_composition.py   # Composition generation
    generate_media.py     # AI media generation
    invoke_agent.py       # Agent invocation logic
    session_service.py    # Session management

  core/                   # App configuration
    config.py             # Environment config
    dependencies.py       # FastAPI dependencies
    security.py           # Auth/security utilities

  models/                 # Pydantic models
    requests/             # Request DTOs
    responses/            # Response DTOs

  prompts/                # LLM prompt templates
    agent_prompts.py      # Agent system prompts
    composition_prompts.py    # Composition generation prompts

  rag/                    # RAG system
    examples/             # Few-shot examples for prompts
    llm_selector.py       # LLM provider selection

  services/               # External service providers
    base/                 # Abstract base classes
      ChatProvider.py
      ImageGenerationProvider.py
      MediaAnalysisProvider.py
      MediaProvider.py
      StorageProvider.py
      VideoGenerationProvider.py
      VoiceGenerationProvider.py
    anthropic/            # Claude integration
    google/               # Gemini, Imagen, VEO, TTS
    openai/               # OpenAI, Whisper
    pexels/               # Stock media
    schemas/              # Response schemas

  tests/                  # Test files
  utils/                  # Utility functions
  migrations/             # SQL migrations
```

## Backend Stack

- FastAPI
- Python 3.12
- uv (package manager)
- Pydantic
- Google Cloud (Vertex AI, GCS)
- Supabase (database)