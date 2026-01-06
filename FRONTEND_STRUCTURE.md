# Frontend Structure Documentation

This document tracks the refactored frontend codebase structure, documenting directories and files as they are cleaned and organized during the Stage 3 deep refactor.

**Last Updated:** January 6, 2026  
**Branch:** `frontend-refactor`

---

## Overview

The frontend is built with:
- **React Router 7** - Full-stack routing framework
- **Vite 7.1.5** - Build tool
- **Remotion 4.0.340** - Video composition engine
- **TypeScript** - Type safety
- **Tailwind CSS + Radix UI** - Styling and components
- **Supabase** - Authentication and storage

---

## Directory Structure

```
app/
├── lib/                    # Core utilities and API configuration
├── hooks/                  # React hooks for state management
├── components/             # React components (in progress)
│   ├── auth/
│   ├── chat/
│   ├── custom-timeline/
│   ├── editor/
│   ├── media/
│   ├── preview/
│   ├── redirects/
│   ├── timeline/
│   └── ui/
├── routes/                 # Page routes (in progress)
├── types/                  # TypeScript type definitions
├── utils/                  # Legacy utilities (being migrated)
├── video-compositions/     # Remotion compositions (in progress)
└── videorender/           # Video rendering logic
```

---

## Refactored Directories

### `app/lib/` - Core Utilities & API

**Purpose:** Core utility functions, API configuration, and service integrations.

**Files:**

| File | Purpose | Key Exports |
|------|---------|-------------|
| `api.ts` | Backend API URL configuration and composition generation | `getBackendUrl()`, `apiUrl()`, `generateComposition()` |
| `authApi.ts` | Authenticated API requests with token management | `authenticatedRequest()`, `getAuthHeaders()`, `getToken()` |
| `sessionApi.ts` | Session persistence (save/load chat sessions) | `createSession()`, `getSession()`, `saveSessionState()`, `listSessions()`, `deleteSession()` |
| `supabase.ts` | Supabase client initialization | `supabase` client instance |
| `utils.ts` | General utility functions | `cn()` (className merger) |
| `uuid.ts` | UUID generation | `generateId()` |

**API Configuration Details (`api.ts`):**
- Development: `http://127.0.0.1:8001` (FastAPI backend)
- Production: Uses `VITE_BACKEND_URL` environment variable or falls back to reverse proxy at `/api`
- Single backend URL (removed dual render/fastapi system)
- Environment detection via `import.meta.env.DEV/PROD`

**Deleted Files:**
- ❌ `fileLogger.ts` (161 lines) - Backend endpoint `/api/v1/logs` doesn't exist, all calls were commented out
- ❌ `media.ts` - Duplicate `MediaBinItem` type definition (moved to `components/editor/timeline/types.ts`)

**Changes:**
- Removed `fixCode()` function from `api.ts` - unused legacy code
- Removed confusing `fastapi` boolean parameter from `apiUrl()` - simplified to single backend
- Updated 16 `apiUrl()` call sites across 6 files to remove boolean parameter
- Fixed imports in `sessionApi.ts` to use `timeline/types` instead of deleted `lib/media`

---

### `app/hooks/` - React State Management

**Purpose:** Custom React hooks for managing application state and side effects.

**Files:**

| File | Purpose | Key Exports |
|------|---------|-------------|
| `useAuth.ts` | Authentication state management | `useAuth()` |
| `useGeminiUpload.ts` | File upload to Google Cloud Storage | `useGeminiUpload()` |
| `useMediaBin.ts` | Media library management (upload, organize) | `useMediaBin()` |
| `useSession.ts` | Session state persistence | `useSession()` |
| `useStandalonePreview.ts` | Standalone video preview | `useStandalonePreview()` |
| `useTimeline.ts` | Timeline state and clip management | `useTimeline()` |
| `useUndoRedo.ts` | Undo/redo functionality | `useUndoRedo()` |

**Hook Details:**

**`useMediaBin.ts`:**
- Handles media file uploads (images, videos, audio)
- Manages media library state with drag-and-drop support
- Integrates with Supabase storage and Google Cloud Storage
- Key functions: `uploadMediaFile()`, `generateMediaFromPrompt()`

**`useSession.ts`:**
- Persists chat sessions and timeline state to backend
- Automatic session creation and recovery
- Handles session listing and deletion
- Serializes/deserializes timeline state

**`useUndoRedo.ts`:**
- Generic undo/redo stack implementation
- Type-safe state management
- Maximum history depth configurable
- API: `set(newState)`, `undo()`, `redo()`, `canUndo`, `canRedo`

**Deleted Files:**
- ❌ `useRenderer.ts` (168 lines) - Referenced non-existent render server on `localhost:8000`, entire codebase uses Remotion for rendering

**Deleted Functions:**
- ❌ `deleteMediaFile()` from `useMediaBin.ts` - Called non-existent render server endpoint
- ❌ `cloneMediaFile()` from `useMediaBin.ts` - Called non-existent render server endpoint  
- ❌ `handleSplitAudio()` from `useMediaBin.ts` - Called non-existent render server endpoint

**Changes:**
- Removed 11 debug `console.log` statements from `useMediaBin.ts`
- Fixed TypeScript error: added type annotation to `percentCompleted` parameter
- Removed `HistoryEntry` interface from `useUndoRedo.ts` - unused type
- Removed `description` parameter from `useUndoRedo.set()` - unused feature
- Updated 9 call sites in `home.tsx` to remove description parameter
- Fixed imports to use correct type locations

---

## Stats

**Files Deleted:** 4  
**Lines Removed:** ~500+  
**Commits:** 4
- `58b7ddd` - Clean up lib/ directory
- `02cfee7` - Remove useRenderer and render server code  
- `130c620` - Clean up hooks directory
- `110363a` - Professional API configuration refactor

**Dead Code Eliminated:**
- Non-existent render server on port 8000 (replaced by Remotion)
- Unused file logging to non-existent backend endpoint
- Duplicate type definitions
- Unused undo/redo description tracking
- 11 debug console.log statements

---

## Environment Variables

```bash
VITE_BACKEND_URL=http://136.115.236.22:8001  # Production backend
VITE_SUPABASE_URL=https://nabgosryybgihawfpkzg.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGci...
```

---

## Next Directories to Refactor

- [ ] `components/editor/` - Editor UI components
- [ ] `components/chat/` - Chat interface
- [ ] `components/timeline/` - Timeline components
- [ ] `video-compositions/` - Remotion compositions
- [ ] `routes/` - Page routes

---

*This document is updated incrementally as refactoring progresses.*
