# Frontend Structure

## Stack

- React Router 7
- Vite 7.1.5
- Remotion 4.0.340
- TypeScript
- Tailwind CSS + Radix UI
- Supabase

## Directories

### `app/lib/`

Core utilities and API configuration.

**Files:**
- `api.ts` - Backend URL configuration, composition generation
- `authApi.ts` - Authenticated requests, token management
- `sessionApi.ts` - Session persistence (save/load)
- `supabase.ts` - Supabase client
- `utils.ts` - General utilities (`cn()`)
- `uuid.ts` - UUID generation

### `app/hooks/`

React hooks for state management.

**Files:**
- `useAuth.ts` - Authentication state
- `useMediaBin.ts` - Media library management
- `useSession.ts` - Session persistence
- `useUndoRedo.ts` - Undo/redo functionality

## Environment

```bash
VITE_BACKEND_URL=http://136.115.236.22:8001
VITE_SUPABASE_URL=https://nabgosryybgihawfpkzg.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGci...
```
