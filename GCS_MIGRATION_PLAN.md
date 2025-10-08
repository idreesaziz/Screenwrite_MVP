# Google Cloud Storage Migration Plan

## Overview
Migrate from local file storage to Google Cloud Storage (GCS) with Supabase JWT authentication. Remove render server dependency and handle all media uploads/downloads through GCS.

---

## Current System Analysis

### Backend Storage Operations

#### 1. **User File Uploads** (`/upload-to-gemini` endpoint)
**Location:** `backend/main.py` (lines 693-813)

**Current Flow:**
- User uploads file via FormData
- For Vertex AI:
  - Creates GCS bucket if needed
  - Uploads to `gs://{project-id}-screenwrite-uploads/uploads/{uuid}.ext`
  - Returns GCS URI
- For Regular Gemini:
  - Saves to temp file
  - Uploads to Gemini Files API
  - Deletes temp file
  - Returns Gemini file ID

**Issues:**
- No user/session isolation in GCS paths
- No authentication required
- Mixed storage strategy (Vertex vs Regular)

#### 2. **Stock Video Downloads** (`/fetch-stock-video` endpoint)
**Location:** `backend/main.py` (lines 1263-1394)

**Current Flow:**
1. Search Pexels API for videos
2. AI curates relevant videos
3. Downloads HIGH quality videos to `backend/out/` directory
4. Serves via `/media/{filename}` static endpoint
5. Returns local URL: `/media/stock_video_{uuid}.mp4`
6. Frontend marks as `upload_status: "pending"`

**Issues:**
- Files downloaded to local disk (`out/` directory)
- No GCS upload
- Files accumulate on server
- No cleanup mechanism

#### 3. **Video Download Helper Functions**
**Location:** `backend/main.py` (lines 199-337)

- `download_video_file_with_retry()` - Downloads to `out/` with retries
- `download_video_file()` - Streams video to local file with integrity check
- `download_and_upload_to_gemini_simultaneously()` - Downloads to memory, uploads to Gemini

**Issues:**
- All use local filesystem (`out/` directory)
- No GCS integration

#### 4. **Generated Content** (`/generate-content` endpoints)
**Location:** `backend/main.py` (lines 1010-1258)

**Current Flow:**
- Generates content via external APIs (Runway, Luma, etc.)
- Downloads generated video using `api_client.files.download()`
- Saves to local `out/` directory
- Returns local URL

**Issues:**
- Generated content stored locally
- No GCS upload
- No user isolation

### Frontend Upload Operations

#### 1. **User File Upload** 
**Location:** `app/hooks/useMediaBin.ts` (lines 153-240)

**Current Flow:**
1. User selects file
2. Extract metadata (duration, dimensions)
3. Create MediaBinItem with `isUploading: true`
4. Upload to render server `/upload` endpoint
5. Render server saves to `out/` directory
6. Render server re-encodes videos for accurate trimming
7. Returns local URL: `/media/{filename}`
8. Update MediaBinItem with `mediaUrlRemote`

**Issues:**
- Uploads to render server (which we're removing)
- Files stored locally
- No GCS integration
- No authentication

#### 2. **Gemini Upload Hook**
**Location:** `app/hooks/useGeminiUpload.ts` (full file)

**Current Flow:**
1. Downloads video from URL (usually stock video)
2. Converts to File/Blob
3. Uploads to backend `/upload-to-gemini`
4. Backend uploads to Gemini Files API or GCS
5. Returns `gemini_file_id`
6. Updates media item status to `uploaded`

**Issues:**
- Downloads entire video to browser memory first
- Inefficient for large files
- Should upload directly to GCS from backend

#### 3. **Media Types**
**Location:** `app/types/media.ts`

```typescript
interface MediaBinItem {
  id: string;
  mediaUrlLocal: string | null;  // Browser blob URL
  mediaUrlRemote: string | null; // Server URL (/media/{filename})
  upload_status: "uploaded" | "not_uploaded" | "pending";
  gemini_file_id: string | null; // For AI analysis
  isUploading: boolean;
  uploadProgress: number | null;
}
```

### Render Server Operations

#### Location: `app/videorender/videorender.ts`

**Current Functionality:**
1. `/upload` - Single file upload with video re-encoding
2. `/upload-multiple` - Bulk upload
3. `/media` - List files
4. `/media/{filename}` - Serve static files
5. `/clone-media` - Copy files
6. `/render` - Render compositions

**To Remove:**
- All upload endpoints
- Static file serving
- File cloning

**To Keep (for now):**
- Render endpoint (but deprioritized)

---

## Migration Strategy

### Phase 1: Authentication Setup

#### 1.1 Supabase Setup (Frontend)
**File:** `app/lib/supabase.ts` (new)

```typescript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
```

#### 1.2 Auth Hook (Frontend)
**File:** `app/hooks/useAuth.ts` (new)

```typescript
import { useState, useEffect } from 'react'
import { supabase } from '~/lib/supabase'
import { User, Session } from '@supabase/supabase-js'

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    })

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
      setUser(session?.user ?? null)
    })

    return () => subscription.unsubscribe()
  }, [])

  return {
    user,
    session,
    loading,
    signIn: (email: string, password: string) => 
      supabase.auth.signInWithPassword({ email, password }),
    signUp: (email: string, password: string) => 
      supabase.auth.signUp({ email, password }),
    signOut: () => supabase.auth.signOut(),
    getToken: async () => {
      const { data: { session } } = await supabase.auth.getSession()
      return session?.access_token ?? null
    }
  }
}
```

#### 1.3 JWT Verification (Backend)
**File:** `backend/auth.py` (new)

```python
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
security = HTTPBearer()

async def verify_jwt(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify Supabase JWT token"""
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"
        )
        return payload  # Contains user_id, email, etc.
    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid authentication credentials: {str(e)}"
        )

async def get_current_user(payload: dict = Depends(verify_jwt)):
    """Extract user info from JWT payload"""
    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
        "session_id": payload.get("session_id")  # For GCS paths
    }
```

### Phase 2: GCS Integration

#### 2.1 GCS Helper Functions (Backend)
**File:** `backend/gcs_storage.py` (new)

```python
from google.cloud import storage
from google.auth import default
import os
import uuid
from typing import Optional
import mimetypes

# Initialize GCS client
credentials, project = default()
storage_client = storage.Client(credentials=credentials, project=project)
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "screenwrite-media")

def get_bucket():
    """Get or create GCS bucket"""
    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        bucket.reload()
        return bucket
    except Exception:
        # Bucket doesn't exist, create it
        bucket = storage_client.create_bucket(
            BUCKET_NAME,
            location=os.getenv("GCS_LOCATION", "us-central1")
        )
        
        # Set lifecycle policy to auto-delete old files (optional)
        bucket.lifecycle_rules = [{
            "action": {"type": "Delete"},
            "condition": {"age": 30}  # Delete files older than 30 days
        }]
        bucket.patch()
        
        print(f"✅ Created GCS bucket: {BUCKET_NAME}")
        return bucket

def upload_file_to_gcs(
    file_content: bytes,
    filename: str,
    user_id: str,
    session_id: str,
    content_type: Optional[str] = None
) -> dict:
    """
    Upload file to GCS with user/session isolation
    
    Returns:
        {
            "gcs_url": "gs://bucket/path",
            "public_url": "https://storage.googleapis.com/bucket/path",
            "filename": "original_filename.ext",
            "size": 12345
        }
    """
    bucket = get_bucket()
    
    # Generate unique filename
    file_extension = os.path.splitext(filename)[1]
    unique_id = str(uuid.uuid4())
    
    # Create isolated path: user_id/session_id/uuid.ext
    blob_path = f"{user_id}/{session_id}/{unique_id}{file_extension}"
    
    # Create blob
    blob = bucket.blob(blob_path)
    
    # Detect content type if not provided
    if not content_type:
        content_type, _ = mimetypes.guess_type(filename)
        content_type = content_type or "application/octet-stream"
    
    # Upload with metadata
    blob.upload_from_string(
        file_content,
        content_type=content_type
    )
    
    # Make publicly readable (or set custom permissions)
    blob.make_public()
    
    print(f"✅ Uploaded to GCS: {blob_path} ({len(file_content)} bytes)")
    
    return {
        "gcs_url": f"gs://{BUCKET_NAME}/{blob_path}",
        "public_url": blob.public_url,
        "filename": filename,
        "size": len(file_content),
        "blob_path": blob_path
    }

async def upload_url_to_gcs(
    url: str,
    filename: str,
    user_id: str,
    session_id: str
) -> dict:
    """Download from URL and upload to GCS"""
    import httpx
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()
        
        content_type = response.headers.get("content-type")
        file_content = response.content
        
        return upload_file_to_gcs(
            file_content,
            filename,
            user_id,
            session_id,
            content_type
        )

def delete_file_from_gcs(blob_path: str) -> bool:
    """Delete file from GCS"""
    try:
        bucket = get_bucket()
        blob = bucket.blob(blob_path)
        blob.delete()
        print(f"✅ Deleted from GCS: {blob_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to delete from GCS: {blob_path} - {e}")
        return False

def get_signed_url(blob_path: str, expiration_minutes: int = 60) -> str:
    """Generate signed URL for temporary access"""
    from datetime import timedelta
    
    bucket = get_bucket()
    blob = bucket.blob(blob_path)
    
    url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=expiration_minutes),
        method="GET"
    )
    
    return url
```

#### 2.2 Update User Upload Endpoint (Backend)
**File:** `backend/main.py` - Modify `/upload-to-gemini`

```python
from auth import get_current_user
from gcs_storage import upload_file_to_gcs

@app.post("/upload-media")
async def upload_media(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """
    Upload user file to GCS with authentication
    Returns GCS URL for frontend use
    """
    print(f"📤 Upload: {file.filename} by user {user['user_id']}")
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Upload to GCS
        result = upload_file_to_gcs(
            file_content=file_content,
            filename=file.filename,
            user_id=user["user_id"],
            session_id=user["session_id"],
            content_type=file.content_type
        )
        
        # Also upload to Gemini for AI analysis (if needed)
        gemini_file_id = None
        if file.content_type.startswith("video/") or file.content_type.startswith("image/"):
            try:
                # Upload to Gemini from GCS URL
                gemini_file_id = await upload_gcs_to_gemini(result["gcs_url"], file.filename)
            except Exception as e:
                print(f"⚠️ Gemini upload failed (non-critical): {e}")
        
        return {
            "success": True,
            "gcs_url": result["gcs_url"],
            "public_url": result["public_url"],
            "filename": result["filename"],
            "size": result["size"],
            "gemini_file_id": gemini_file_id
        }
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

#### 2.3 Update Stock Video Endpoint (Backend)
**File:** `backend/main.py` - Modify `/fetch-stock-video`

```python
@app.post("/fetch-stock-video")
async def fetch_stock_video(
    request: FetchStockVideoRequest,
    user: dict = Depends(get_current_user)  # Add auth
):
    """
    Fetch stock videos and upload directly to GCS
    No local storage
    """
    print(f"🔍 Fetch stock videos for: {user['user_id']}")
    
    try:
        # Search and curate videos (existing logic)
        search_results = await search_pexels_videos(request.query, per_page=50)
        videos_data = search_results.get("videos", [])
        curation_result = await curate_videos_with_ai(videos_data, request.query, max_count=4)
        selected_videos = [videos_data[i] for i in curation_result["selected"]]
        
        async def process_video(video, index):
            """Download and upload directly to GCS"""
            video_files = video.get("video_files", [])
            best_file = select_best_video_file(video_files)
            
            # Generate filename
            asset_id = str(uuid.uuid4())
            filename = f"stock_video_{asset_id}.mp4"
            
            print(f"📥 Processing video {index+1}: {filename}")
            
            # Upload URL directly to GCS (no local storage)
            gcs_result = await upload_url_to_gcs(
                url=best_file["link"],
                filename=filename,
                user_id=user["user_id"],
                session_id=user["session_id"]
            )
            
            # Upload to Gemini for AI analysis
            gemini_file_id = None
            try:
                gemini_file_id = await upload_gcs_to_gemini(
                    gcs_result["gcs_url"],
                    filename
                )
            except Exception as e:
                print(f"⚠️ Gemini upload failed (non-critical): {e}")
            
            return StockVideoResult(
                id=video["id"],
                pexels_url=video.get("url", ""),
                download_url=gcs_result["public_url"],  # GCS public URL
                preview_image=video.get("image", ""),
                duration=video.get("duration", 0),
                width=best_file.get("width", 0),
                height=best_file.get("height", 0),
                file_type=best_file.get("file_type", "video/mp4"),
                quality=best_file.get("quality", "sd") or "sd",
                photographer=video.get("user", {}).get("name", "Unknown"),
                photographer_url=video.get("user", {}).get("url", ""),
                upload_status="uploaded",  # Already in GCS
                gemini_file_id=gemini_file_id
            )
        
        # Process all videos in parallel
        tasks = [process_video(v, i) for i, v in enumerate(selected_videos)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        stock_results = [r for r in results if not isinstance(r, Exception)]
        
        return FetchStockVideoResponse(
            success=True,
            query=request.query,
            videos=stock_results,
            total_results=len(videos_data),
            ai_curation_explanation=curation_result["explanation"]
        )
        
    except Exception as e:
        print(f"❌ Stock video fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

#### 2.4 Update Generated Content Endpoint (Backend)
**File:** `backend/main.py` - Modify `/generate-content`

```python
@app.post("/generate-content")
async def generate_content(
    request: GenerateContentRequest,
    user: dict = Depends(get_current_user)  # Add auth
):
    """
    Generate content and upload to GCS
    """
    try:
        # Generate content (existing logic)
        # ...
        
        # Download generated video to memory
        video_data = content_generator.api_client.files.download(
            file=generated_video.video
        )
        
        # Upload to GCS
        gcs_result = upload_file_to_gcs(
            file_content=video_data,
            filename=f"generated_{uuid.uuid4()}.mp4",
            user_id=user["user_id"],
            session_id=user["session_id"],
            content_type="video/mp4"
        )
        
        # Upload to Gemini if needed
        gemini_file_id = await upload_gcs_to_gemini(
            gcs_result["gcs_url"],
            gcs_result["filename"]
        )
        
        return GenerateContentResponse(
            success=True,
            video_url=gcs_result["public_url"],  # GCS URL
            gemini_file_id=gemini_file_id,
            # ... other fields
        )
        
    except Exception as e:
        print(f"❌ Generate content error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Phase 3: Frontend Updates

#### 3.1 Update Media Upload Hook (Frontend)
**File:** `app/hooks/useMediaBin.ts` - Modify `handleAddMediaToBin`

```typescript
import { useAuth } from '~/hooks/useAuth'

export const useMediaBin = (handleDeleteScrubbersByMediaBinId: (mediaBinId: string) => void) => {
  const { getToken } = useAuth()  // Add auth hook
  
  const handleAddMediaToBin = useCallback(async (file: File) => {
    const id = generateUUID();
    const name = file.name;
    let mediaType: "video" | "image" | "audio";
    // ... determine media type
    
    try {
      const mediaUrlLocal = URL.createObjectURL(file);
      const metadata = await getMediaMetadata(file, mediaType);
      
      // Add to media bin immediately
      const newItem: MediaBinItem = {
        id,
        name,
        mediaType,
        mediaUrlLocal,
        mediaUrlRemote: null,  // Will be GCS URL
        durationInSeconds: metadata.durationInSeconds ?? 0,
        media_width: metadata.width,
        media_height: metadata.height,
        text: null,
        isUploading: true,
        uploadProgress: 0,
        upload_status: "pending",
        left_transition_id: null,
        right_transition_id: null,
        gemini_file_id: null,
      };
      setMediaBinItems(prev => [...prev, newItem]);
      
      // Get JWT token
      const token = await getToken()
      if (!token) {
        throw new Error("Not authenticated")
      }
      
      // Upload to backend (which uploads to GCS)
      const formData = new FormData();
      formData.append('file', file);
      
      const uploadResponse = await axios.post(
        apiUrl('/upload-media', true),  // Backend endpoint
        formData,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const percentCompleted = Math.round(
                (progressEvent.loaded * 100) / progressEvent.total
              );
              
              setMediaBinItems(prev =>
                prev.map(item =>
                  item.id === id
                    ? { ...item, uploadProgress: percentCompleted }
                    : item
                )
              );
            }
          }
        }
      );
      
      // Update with GCS URLs
      setMediaBinItems(prev =>
        prev.map(item =>
          item.id === id
            ? {
                ...item,
                mediaUrlRemote: uploadResponse.data.public_url,  // GCS public URL
                isUploading: false,
                uploadProgress: 100,
                upload_status: "uploaded",
                gemini_file_id: uploadResponse.data.gemini_file_id
              }
            : item
        )
      );
      
      console.log("✅ Uploaded to GCS:", uploadResponse.data.public_url);
      
    } catch (error) {
      console.error("Upload failed:", error);
      // Handle error...
    }
  }, [getToken]);
  
  return {
    mediaBinItems,
    handleAddMediaToBin,
    // ... other methods
  };
};
```

#### 3.2 Update API Util (Frontend)
**File:** `app/utils/api.ts` - Add auth header helper

```typescript
export const getAuthHeaders = async (getToken: () => Promise<string | null>) => {
  const token = await getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

// Update apiUrl to support auth
export const apiUrl = (path: string, useBackend: boolean = false) => {
  const base = useBackend 
    ? import.meta.env.VITE_BACKEND_URL || 'http://localhost:8001'
    : import.meta.env.VITE_RENDER_URL || 'http://localhost:5000'
  return `${base}${path}`
}
```

#### 3.3 Remove Render Server Dependencies (Frontend)
**Files to update:**
- Remove `/upload` calls to render server
- Update all media URLs to use GCS public URLs
- Remove render server URL from env

### Phase 4: Cleanup

#### 4.1 Remove Local Storage (Backend)
- Delete `backend/out/` directory
- Remove static file mounting: `app.mount("/media", StaticFiles(...))`
- Remove download functions that write to disk
- Keep only in-memory operations

#### 4.2 Remove/Deprecate Render Server
**File:** `app/videorender/videorender.ts`
- Remove upload endpoints
- Remove static file serving
- Keep render endpoint (but mark as deprecated)

#### 4.3 Update Documentation
- Update README with GCS setup instructions
- Document authentication flow
- Add GCS bucket setup guide
- Add Supabase setup guide

---

## Implementation Checklist

### Authentication
- [ ] Install Supabase client: `npm install @supabase/supabase-js`
- [ ] Create `app/lib/supabase.ts`
- [ ] Create `app/hooks/useAuth.ts`
- [ ] Install JWT library in backend: `pip install python-jose[cryptography]`
- [ ] Create `backend/auth.py`
- [ ] Add Supabase env vars to `.env`
- [ ] Test JWT verification

### Backend GCS Integration
- [ ] Install GCS library: `pip install google-cloud-storage`
- [ ] Create `backend/gcs_storage.py`
- [ ] Create GCS bucket (or auto-create on first use)
- [ ] Update `/upload-to-gemini` → `/upload-media` with auth
- [ ] Update `/fetch-stock-video` with GCS upload
- [ ] Update `/generate-content` with GCS upload
- [ ] Remove static file mounting
- [ ] Remove local file download functions
- [ ] Test GCS uploads

### Frontend Updates
- [ ] Update `useMediaBin` to use new `/upload-media` endpoint
- [ ] Add authentication to all upload calls
- [ ] Update media URLs to use GCS public URLs
- [ ] Remove render server dependencies
- [ ] Update `apiUrl` utility
- [ ] Test user file uploads

### Cleanup
- [ ] Delete `backend/out/` directory
- [ ] Remove render server upload endpoints
- [ ] Update environment variables
- [ ] Remove unused dependencies
- [ ] Update documentation

### Testing
- [ ] Test user authentication flow
- [ ] Test user file upload to GCS
- [ ] Test stock video fetch and GCS storage
- [ ] Test generated content GCS storage
- [ ] Test JWT authentication on all endpoints
- [ ] Test user/session isolation in GCS paths
- [ ] Load test GCS performance
- [ ] Test error handling
- [ ] Test cleanup/deletion

---

## Environment Variables

### Frontend (`.env`)
```bash
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_BACKEND_URL=http://localhost:8001
```

### Backend (`.env`)
```bash
# Supabase
SUPABASE_JWT_SECRET=your-jwt-secret

# GCS
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GCS_BUCKET_NAME=screenwrite-media
GCS_LOCATION=us-central1
GCS_PROJECT_ID=your-project-id

# Existing
GEMINI_API_KEY=...
PEXELS_API_KEY=...
```

---

## Migration Benefits

1. **Scalability:** GCS handles unlimited storage with CDN integration
2. **Security:** JWT authentication isolates user data
3. **Cost:** Pay only for storage used, no server disk costs
4. **Reliability:** GCS provides 99.999999999% durability
5. **Performance:** GCS global CDN for fast media delivery
6. **Cleanup:** Automatic lifecycle policies delete old files
7. **Simplicity:** No render server maintenance

---

## Rollback Plan

If migration fails:
1. Keep old endpoints alongside new ones
2. Add feature flag: `USE_GCS=true/false`
3. Gradual rollout per user
4. Monitor error rates
5. Rollback if errors > 5%

---

## Post-Migration

### Monitoring
- Monitor GCS usage and costs
- Track upload/download latency
- Monitor authentication failures
- Set up alerts for quota limits

### Optimization
- Implement CDN caching
- Add image/video optimization
- Implement lazy loading
- Add progress tracking
- Implement resume uploads for large files

### Future Enhancements
- Add file versioning
- Add file sharing between users
- Add collaborative workspaces
- Add media library search
- Add automatic transcoding
