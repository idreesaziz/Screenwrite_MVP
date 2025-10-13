# Frontend Endpoint Migration - Completed

## Summary
Updated all frontend code to use the new backend API endpoints (v2.0.0).

## Backend Changes

### Added Agent Router
- **File:** `backend/main.py`
- **Change:** Added `agent_router` with prefix `/api/v1/agent`

## Frontend Endpoint Updates

### 1. Authentication & Upload
| Old Endpoint | New Endpoint | File | Status |
|-------------|--------------|------|--------|
| `/upload-media` | `/api/v1/upload/upload` | `app/utils/authApi.ts` | ✅ Updated |

### 2. Composition Generation
| Old Endpoint | New Endpoint | File | Status |
|-------------|--------------|------|--------|
| `/ai/generate-composition` | `/api/v1/compositions/generate` | `app/utils/api.ts` | ✅ Updated |
| `/ai/generate-composition` | `/api/v1/compositions/generate` | `app/routes/home.tsx` | ✅ Updated |

### 3. Agent/Chat
| Old Endpoint | New Endpoint | File | Status |
|-------------|--------------|------|--------|
| `/ai/agent` | `/api/v1/agent/chat` | `app/components/chat/ConversationalSynth.ts` | ✅ Updated |
| `/ai` | `/api/v1/agent/chat` | `app/components/chat/ChatBox.tsx` | ✅ Updated (with TODO) |

### 4. Media Analysis
| Old Endpoint | New Endpoint | File | Status |
|-------------|--------------|------|--------|
| `/analyze-video` | `/api/v1/analysis/media` | `app/components/chat/ChatBox.tsx` (2 locations) | ✅ Updated |

### 5. Media Generation
| Old Endpoint | New Endpoint | File | Status |
|-------------|--------------|------|--------|
| `/generate-content` | `/api/v1/media/generate` | `app/components/chat/ChatBox.tsx` | ✅ Updated |

### 6. Stock Media
| Old Endpoint | New Endpoint | File | Status |
|-------------|--------------|------|--------|
| `/fetch-stock-video` | `/api/v1/stock/search` | `app/components/chat/ChatBox.tsx` | ✅ Updated |

### 7. Deprecated Endpoints
| Old Endpoint | Status | File | Action |
|-------------|--------|------|--------|
| `/upload-to-gemini` | DEPRECATED | `app/hooks/useGeminiUpload.ts` | Added deprecation notice |
| `/chat/log` | NOT IMPLEMENTED | `app/utils/fileLogger.ts` | Commented out with TODO |
| `/ai/fix-code` | NOT FOUND | `app/utils/api.ts` | Needs clarification |

### 8. Render Server (Separate - Port 8000)
These endpoints remain on the Node.js render server (port 8000):

| Endpoint | File | Notes |
|----------|------|-------|
| `/health` | `app/hooks/useRenderer.ts` | Explicitly uses `apiUrl(..., false)` |
| `/render` | `app/hooks/useRenderer.ts` | Explicitly uses `apiUrl(..., false)` |
| `/media/{filename}` (DELETE) | `app/hooks/useMediaBin.ts` | Explicitly uses `apiUrl(..., false)` |
| `/clone-media` | `app/hooks/useMediaBin.ts` | Explicitly uses `apiUrl(..., false)` |

## API URL Configuration

The `apiUrl()` function in `app/utils/api.ts` now accepts a second parameter:
- `apiUrl(endpoint, true)` → FastAPI backend (port 8001)
- `apiUrl(endpoint, false)` → Node.js render server (port 8000)

### Production URLs
- FastAPI: `${window.location.origin}/ai/api`
- Node.js: `${window.location.origin}/api`

### Development URLs
- FastAPI: `http://127.0.0.1:8001`
- Node.js: `http://localhost:8000`

## New Backend API Structure

### Available Routers
1. `/api/v1/analysis` - Media analysis endpoints
   - `POST /media` - Analyze media (video, image, audio, documents)

2. `/api/v1/compositions` - Composition generation
   - `POST /generate` - Generate/modify video compositions

3. `/api/v1/stock` - Stock media search
   - `POST /search` - Search and curate stock videos/images

4. `/api/v1/media` - Media generation
   - `POST /generate` - Generate images (sync) or videos (async)
   - `GET /status/{operation_id}` - Poll video generation status

5. `/api/v1/upload` - File uploads
   - `POST /upload` - Upload media to GCS with user/session isolation

6. `/api/v1/agent` - Conversational agent
   - `POST /chat` - Chat with AI video editing agent

7. `/api/v1/health` - Health check

## TODO Items

### High Priority
1. **Fix Code Endpoint Missing**
   - File: `app/utils/api.ts`
   - The `/ai/fix-code` endpoint doesn't exist in new backend
   - Used in: `app/hooks/useStandalonePreview.ts`
   - Action: Either implement in backend or remove from frontend

2. **Chat Logging**
   - File: `app/utils/fileLogger.ts`
   - The `/chat/log` endpoint doesn't exist in new backend
   - Action: Decide if chat logging is needed, implement if yes

3. **Agent Endpoint Compatibility**
   - File: `app/components/chat/ChatBox.tsx` (line ~1217)
   - Old timeline-based AI code updated to use `/api/v1/agent/chat`
   - The request format may need adjustment to match new agent API
   - Action: Test and verify request/response format matches

### Medium Priority
1. **Stock Search Request Format**
   - File: `app/components/chat/ChatBox.tsx`
   - Added `media_type: "video"` to request
   - Verify this matches backend expectations

2. **Gemini Upload Deprecation**
   - File: `app/hooks/useGeminiUpload.ts`
   - Marked as deprecated but still in codebase
   - Action: Remove if no longer used

### Low Priority
1. **Type Definitions**
   - Update TypeScript types to match new API responses
   - Some response formats may have changed

## Testing Checklist

- [ ] File upload to GCS works
- [ ] Composition generation works
- [ ] Agent chat works
- [ ] Media analysis works
- [ ] Image generation works (sync)
- [ ] Video generation works (async with polling)
- [ ] Stock media search works
- [ ] Video rendering still works (separate server)
- [ ] Media deletion works (separate server)
- [ ] Media cloning works (separate server)

## Notes

1. **Two Servers Running:**
   - FastAPI backend (port 8001): New AI/generation features
   - Node.js render server (port 8000): Video rendering with Remotion

2. **Authentication:**
   - All new endpoints require JWT authentication via Supabase
   - Token passed in `Authorization: Bearer <token>` header

3. **GCS Storage:**
   - Files now uploaded directly to GCS (not Gemini)
   - Path format: `user_id/session_id/filename`
   - Gemini can access GCS URLs directly for analysis

4. **Async Operations:**
   - Video generation is async (returns operation_id)
   - Poll `/api/v1/media/status/{operation_id}` for status

## Breaking Changes

1. Response format may have changed for some endpoints
2. Request format may have changed for some endpoints
3. Error responses now follow FastAPI format
4. Gemini upload flow removed (now uses GCS directly)
