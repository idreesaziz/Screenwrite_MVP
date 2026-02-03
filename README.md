# Screenwrite

Screenwrite is an AI‑assisted video editor that blends a timeline UI with a programmable composition engine. It translates natural‑language edits into a structured Remotion blueprint, then renders clips, transitions, and animated text deterministically. The goal is to make advanced video workflows reproducible, editable, and inspectable as code.

## Highlights
- **Blueprint composition engine** with track/clip models, adjacency‑aware transitions, and orphaned transition handling.
- **Element DSL + renderer**: string‑based elements parsed into flat → nested trees and rendered through a typed component registry.
- **Animation system**: `@animate[...]` keyframes supporting numeric, color, and complex CSS transform interpolation.
- **AI composition pipeline**: structured JSON output, overlap resolution, and aspect‑ratio safeguards before the editor consumes results.
- **Provider‑agnostic backend**: Gemini/Claude/OpenAI chat providers wired behind a shared `ChatProvider` interface.

## Tech Stack
**Frontend:** React Router 7 (SSR), Vite, Remotion 4, TypeScript, Tailwind, Radix UI  
**Backend:** FastAPI, Python 3.12, `uv`, Pydantic  
**AI / Media:** Google Vertex AI (Gemini/Imagen/Veo), Pexels, Supabase Auth, GCS

---

# Setup

## Prerequisites
- Node.js 20+
- `pnpm`
- Python 3.12
- Google Cloud service account (Vertex AI + GCS access)

## 1) Frontend
```bash
pnpm install
pnpm dev
```

## 2) Backend
```bash
cd backend
uv sync
uv run uvicorn main:app --host 0.0.0.0 --port 8001 --timeout-keep-alive 600
```

---

# Environment Variables

## Frontend (`.env`)
```dotenv
VITE_SUPABASE_URL=...
VITE_SUPABASE_ANON_KEY=...
VITE_BACKEND_URL=http://localhost:8001
```

## Backend (`backend/.env`)
**Required (minimal path):**
- `GOOGLE_APPLICATION_CREDENTIALS` — path to service account JSON
- `GOOGLE_CLOUD_PROJECT`
- `GOOGLE_CLOUD_LOCATION`
- `GCS_BUCKET_NAME`
- `SUPABASE_URL`
- `SUPABASE_JWT_SECRET`
- `SUPABASE_SERVICE_KEY`

**Optional (only if you want these services):**
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `PEXELS_API_KEY`

---

# Project Structure (High‑Level)
```
app/                  # Frontend (editor UI + Remotion player)
  composition/        # Blueprint renderer + element execution
  components/         # Editor UI, timeline, chat, panels
  hooks/              # Editor and AI workflow hooks
backend/              # FastAPI services
  api/                # REST routers
  business_logic/     # AI orchestration and composition editing
  services/           # Provider implementations
```

---

# Running the App
- Frontend runs on the React Router dev server.
- Backend runs on `http://localhost:8001`.
- Ensure `VITE_BACKEND_URL` points to the backend.

---

# How It Works (Technical Overview)
- **Composition Blueprint:** track/clip timeline with transition metadata.
- **Element System:** components authored as string elements, parsed into flat → nested trees, rendered via a registry.
- **Animation Layer:** `@animate[...]` resolves to interpolated values at render‑time.
- **AI Generation:** structured JSON response is validated, overlap‑corrected, and pushed to the editor.

---

# System Architecture

Screenwrite is split into a **deterministic render core** and an **AI orchestration layer**, with a thin UI shell for editing and inspection.

## 1) Frontend (React Router + Remotion)
- **Editor shell** (`app/routes/Home.tsx`) manages layout, state, and tool orchestration.
- **Composition engine** (`app/composition/*`) renders a blueprint into Remotion sequences, handling adjacent and orphaned transitions for clean clip boundaries.
- **Element pipeline** parses a compact element DSL into a flat tree, converts it to nested objects, then renders via a typed component registry.
- **Animation resolver** interpolates numbers, colors, and complex CSS transforms at render‑time using `@animate[...]`.

## 2) Backend (FastAPI orchestration)
- **Composition service** builds a strict system prompt + JSON schema, calls the LLM, validates output, fixes overlaps, and normalizes aspect ratios.
- **Provider abstraction** (`ChatProvider`) allows swapping Gemini/Claude/OpenAI without changing orchestration code.
- **Media and storage services** integrate GCS for assets and optional Pexels for stock media.

## 3) Data Flow (end‑to‑end)
1. User edits in the UI or via chat.
2. Backend generates/edits a **composition blueprint** (track/clip array with element strings).
3. Frontend renders the blueprint through the composition engine for live preview.
4. The same blueprint can be persisted, replayed, or re‑edited deterministically.

## 4) Design Rationale
- **Blueprints as the source of truth** keep AI output auditable and versionable.
- **DSL‑based elements** make AI outputs compact while remaining deterministic.
- **Rendering is pure**: no side effects, enabling predictable previews and exports.

---

# License
See `LICENSE`.
