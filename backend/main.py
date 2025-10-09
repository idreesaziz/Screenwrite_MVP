import os
import subprocess
import tempfile
import json
import time
import re
import shutil
import uuid
import requests
import asyncio
import httpx
from PIL import Image
from io import BytesIO

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Import code generation functionality
from code_generator import generate_composition_with_validation
import code_generator  # Keep for other functions like parse_ai_response

from schema import (
    TextProperties, BaseScrubber, 
    GenerateContentRequest, GenerateContentResponse, GeneratedAsset,
    CheckGenerationStatusRequest, CheckGenerationStatusResponse,
    FetchStockVideoRequest, FetchStockVideoResponse, StockVideoResult
)
from providers import ContentGenerationProvider
from auth import get_current_user
from fastapi import Depends
from gcs_storage import upload_file_to_gcs, upload_url_to_gcs

load_dotenv()

# Get API key (used for both regular and Vertex AI fallback)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

# Check if we should use Vertex AI
USE_VERTEX_AI = os.getenv("USE_VERTEX_AI", "false").lower() == "true"

# Use Vertex AI if flag is set
if USE_VERTEX_AI:
    # For Vertex AI fine-tuned models, we'll initialize in code_generator.py
    # Keep a dummy client here for compatibility
    gemini_api = genai.Client(api_key=GEMINI_API_KEY)  # Fallback client
    # Cloud Storage will be imported when needed
    storage_bucket_name = f"{os.getenv('VERTEX_PROJECT_ID', '24816576653')}-screenwrite-uploads"
    print(f"🔥 Using Vertex AI Fine-tuned Model - Project: {os.getenv('VERTEX_PROJECT_ID', '24816576653')}, Location: {os.getenv('VERTEX_LOCATION', 'europe-west1')}")
else:
    # Use regular Gemini API
    gemini_api = genai.Client(api_key=GEMINI_API_KEY)
    storage_bucket_name = None
    print("🔥 Using regular Gemini API")

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure output directory exists before mounting static files
out_dir = os.path.abspath("out")
os.makedirs(out_dir, exist_ok=True)
print(f"📁 Static files directory: {out_dir}")

# Mount static file serving for generated media
app.mount("/media", StaticFiles(directory=out_dir), name="media")


# Test endpoint for authentication
@app.get("/test-auth")
async def test_auth(user: dict = Depends(get_current_user)):
    """Test endpoint to verify JWT authentication is working"""
    return {
        "success": True,
        "message": "Authentication successful!",
        "user_id": user.get("user_id"),
        "email": user.get("email"),
        "session_id": user.get("session_id"),
        "role": user.get("role"),
        "user": user  # Full user object for debugging
    }


# Unified media upload endpoint with JWT authentication
@app.post("/upload-media")
async def upload_media(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """
    Unified endpoint for uploading media files to GCS.
    All uploads are isolated by user_id and session_id from JWT.
    
    Accepts: images, videos, audio files
    Returns: GCS public URL
    """
    try:
        # Extract user info from JWT
        user_id = user.get("user_id")
        session_id = user.get("session_id")
        
        if not user_id or not session_id:
            raise HTTPException(
                status_code=400,
                detail="Invalid JWT: missing user_id or session_id"
            )
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Get content type
        content_type = file.content_type or "application/octet-stream"
        
        print(f"📤 Uploading {file.filename} for user {user_id}, session {session_id}")
        
        # Upload to GCS
        gcs_url = upload_file_to_gcs(
            file_data=file.file,
            user_id=user_id,
            session_id=session_id,
            filename=file.filename,
            content_type=content_type
        )
        
        print(f"✅ Upload successful: {gcs_url}")
        
        return {
            "success": True,
            "url": gcs_url,
            "filename": file.filename,
            "content_type": content_type,
            "user_id": user_id,
            "session_id": session_id
        }
        
    except Exception as e:
        print(f"❌ Upload failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )


# Pexels API Helper Functions
async def search_pexels_videos(query: str, per_page: int = 3):
    """Search Pexels for landscape videos using their API"""
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Pexels API key not configured")
    
    # Remove quotes if present (from .env file)
    api_key = api_key.strip('"\'')
    
    headers = {"Authorization": api_key}  # Pexels expects just the API key, not "Bearer"
    params = {
        "query": query,
        "per_page": per_page,  # Configurable number of results
        "orientation": "landscape"  # Enforce landscape only
    }
    
    try:
        print(f"🔍 Pexels API call: {query} (key: {api_key[:8]}...)")
        response = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params, timeout=30)
        print(f"📡 Response status: {response.status_code}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"❌ Pexels API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Pexels API request failed: {str(e)}")


def select_best_video_file(video_files: List[Dict]) -> Dict:
    """Select the best quality video file from available options"""
    if not video_files:
        return None
    
    # Priority: HD mp4 > SD mp4 > others
    hd_mp4 = [f for f in video_files if f.get("quality") == "hd" and f.get("file_type") == "video/mp4"]
    if hd_mp4:
        # Prefer standard resolutions (1920x1080, 1280x720)
        preferred = [f for f in hd_mp4 if f.get("width") in [1920, 1280]]
        return preferred[0] if preferred else hd_mp4[0]
    
    # Fallback to SD mp4
    sd_mp4 = [f for f in video_files if f.get("quality") == "sd" and f.get("file_type") == "video/mp4"]
    return sd_mp4[0] if sd_mp4 else video_files[0]


def select_lowest_quality_video_file(video_files: List[Dict]) -> Dict:
    """Select the lowest quality video file for fast Gemini uploads"""
    if not video_files:
        return None
    
    # Priority for Gemini: Smallest file size (lowest quality, smallest resolution)
    mp4_files = [f for f in video_files if f.get("file_type") == "video/mp4"]
    if not mp4_files:
        return video_files[0] if video_files else None
    
    # Sort by quality (sd before hd) and resolution (smaller first)
    def quality_score(file):
        # Lower score = prefer for Gemini upload
        quality = file.get("quality", "sd")
        width = file.get("width", 0)
        
        quality_score = 0 if quality == "sd" else 1  # Prefer SD over HD
        resolution_score = width / 1000  # Lower resolution preferred
        
        return quality_score + resolution_score
    
    # Return the file with the lowest quality score
    return min(mp4_files, key=quality_score)


async def upload_url_to_gemini_directly(url: str, filename: str, client: httpx.AsyncClient = None) -> str:
    """
    Stream video directly from Pexels URL to Gemini without local storage.
    Optimized for fast Gemini uploads using lowest quality files.
    Returns gemini_file_id
    """
    try:
        print(f"📤 Direct streaming to Gemini: {url}")
        
        if client:
            # Use shared client for connection reuse
            async with client.stream('GET', url, follow_redirects=True) as response:
                response.raise_for_status()
                
                # Stream directly to memory for Gemini upload
                gemini_buffer = BytesIO()
                
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    gemini_buffer.write(chunk)
                
                # Upload to Gemini from memory buffer
                gemini_buffer.seek(0)
                gemini_file_id = await upload_file_content_to_gemini(gemini_buffer.getvalue(), filename)
                
                print(f"✅ Direct Gemini upload completed: {filename} -> {gemini_file_id}")
                return gemini_file_id
        else:
            # Fallback to individual client
            timeout = httpx.Timeout(60.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream('GET', url, follow_redirects=True) as response:
                    response.raise_for_status()
                    
                    # Stream directly to memory for Gemini upload
                    gemini_buffer = BytesIO()
                    
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        gemini_buffer.write(chunk)
                    
                    # Upload to Gemini from memory buffer
                    gemini_buffer.seek(0)
                    gemini_file_id = await upload_file_content_to_gemini(gemini_buffer.getvalue(), filename)
                    
                    print(f"✅ Direct Gemini upload completed: {filename} -> {gemini_file_id}")
                    return gemini_file_id
                
    except Exception as e:
        print(f"❌ Direct Gemini upload failed for {url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload directly to Gemini: {str(e)}")


async def download_video_file_with_retry(url: str, filename: str, client: httpx.AsyncClient = None, max_retries: int = 3) -> str:
    """Download video file with retry mechanism for reliability"""
    last_error = None
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                print(f"🔄 Retry attempt {attempt + 1}/{max_retries} for {filename}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff: 2s, 4s, 8s
            
            return await download_video_file(url, filename, client)
            
        except Exception as e:
            last_error = e
            print(f"❌ Download attempt {attempt + 1} failed: {str(e)}")
            
            # If this was the last attempt, re-raise the error
            if attempt == max_retries - 1:
                break
    
    # All retries failed
    print(f"💥 All {max_retries} download attempts failed for {filename}")
    raise HTTPException(status_code=500, detail=f"Failed to download after {max_retries} attempts: {str(last_error)}")


async def download_video_file(url: str, filename: str, client: httpx.AsyncClient = None) -> str:
    """Download video file from Pexels/Vimeo URL with streaming and integrity verification"""
    try:
        # Use absolute path to ensure directory is created in the right place
        out_dir = os.path.abspath("out")
        filepath = os.path.join(out_dir, filename)
        temp_filepath = f"{filepath}.tmp"  # Use temporary file during download
        os.makedirs(out_dir, exist_ok=True)
        
        print(f"📁 Creating output directory: {out_dir}")
        print(f"💾 Streaming download to: {filepath}")
        
        # Remove any existing temp file
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        
        if client:
            # Use shared client for connection reuse with streaming
            async with client.stream('GET', url, follow_redirects=True) as response:
                response.raise_for_status()
                
                # Get expected file size from headers
                expected_size = None
                if 'content-length' in response.headers:
                    expected_size = int(response.headers['content-length'])
                    print(f"📏 Expected file size: {expected_size} bytes")
                
                # Stream download to temporary file
                downloaded_size = 0
                with open(temp_filepath, 'wb') as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):  # 8KB chunks
                        f.write(chunk)
                        downloaded_size += len(chunk)
                
                # Verify download integrity
                if expected_size and downloaded_size != expected_size:
                    raise Exception(f"Download incomplete: expected {expected_size} bytes, got {downloaded_size} bytes")
                
                print(f"✅ Streaming download completed: {downloaded_size} bytes")
        else:
            # Fallback to individual client with streaming
            timeout = httpx.Timeout(120.0)  # Increased timeout for large files
            async with httpx.AsyncClient(timeout=timeout) as individual_client:
                async with individual_client.stream('GET', url, follow_redirects=True) as response:
                    response.raise_for_status()
                    
                    # Get expected file size from headers
                    expected_size = None
                    if 'content-length' in response.headers:
                        expected_size = int(response.headers['content-length'])
                        print(f"📏 Expected file size: {expected_size} bytes")
                    
                    # Stream download to temporary file
                    downloaded_size = 0
                    with open(temp_filepath, 'wb') as f:
                        async for chunk in response.aiter_bytes(chunk_size=8192):  # 8KB chunks
                            f.write(chunk)
                            downloaded_size += len(chunk)
                    
                    # Verify download integrity
                    if expected_size and downloaded_size != expected_size:
                        raise Exception(f"Download incomplete: expected {expected_size} bytes, got {downloaded_size} bytes")
                    
                    print(f"✅ Streaming download completed: {downloaded_size} bytes")
        
        # Atomic move: rename temp file to final file (prevents partial file access)
        os.rename(temp_filepath, filepath)
        
        # Final verification with basic video file validation
        if not os.path.exists(filepath):
            raise Exception(f"File was not created after move: {filepath}")
        
        final_file_size = os.path.getsize(filepath)
        if final_file_size == 0:
            raise Exception(f"Final file is empty: {filepath}")
        
        # Basic video file format validation
        if final_file_size < 1024:  # Less than 1KB is definitely not a video
            raise Exception(f"File too small to be a valid video: {final_file_size} bytes")
        
        # Check if file starts with valid video headers (basic corruption detection)
        try:
            with open(filepath, 'rb') as f:
                file_header = f.read(8)
                # Check for common video file signatures
                if len(file_header) < 4:
                    raise Exception("File header too short")
                
                # MP4 files typically start with specific bytes
                # This is a basic check, not comprehensive
                if not (file_header.startswith(b'\x00\x00\x00') or  # MP4 ftyp box
                       file_header.startswith(b'ftyp') or           # MP4 ftyp
                       file_header.startswith(b'\x1a\x45\xdf\xa3') or  # WebM/MKV
                       file_header.startswith(b'RIFF')):            # AVI
                    print(f"⚠️ Warning: Unexpected file header for video file: {file_header.hex()}")
                    # Don't fail here, just warn - some valid videos might not match these patterns
        except Exception as header_check_error:
            print(f"⚠️ Could not verify file header (file may still be valid): {header_check_error}")
        
        print(f"🔍 File verification passed: {filepath} ({final_file_size} bytes)")
        return filepath
        
    except Exception as e:
        # Cleanup temporary file on error
        if os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
                print(f"🧹 Cleaned up temporary file: {temp_filepath}")
            except:
                pass
        
        print(f"❌ Download failed for {url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download video: {str(e)}")


async def download_and_upload_to_gemini_simultaneously(url: str, filename: str) -> tuple[str, str]:
    """
    Download video from URL and upload to Gemini simultaneously for optimal performance.
    Returns (local_filepath, gemini_file_id)
    """
    try:
        filepath = os.path.join("out", filename)
        os.makedirs("out", exist_ok=True)
        
        print(f"📥 Downloading and uploading to Gemini: {url}")
        
        timeout = httpx.Timeout(60.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream('GET', url, follow_redirects=True) as response:
                response.raise_for_status()
                
                # Prepare both destinations
                local_file = open(filepath, 'wb')
                gemini_buffer = BytesIO()
                
                # Stream to both local disk and memory simultaneously
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    local_file.write(chunk)      # → Local disk
                    gemini_buffer.write(chunk)   # → Memory for Gemini
                
                local_file.close()
                
                # Upload to Gemini from memory buffer
                gemini_buffer.seek(0)
                gemini_file_id = await upload_file_content_to_gemini(gemini_buffer.getvalue(), filename)
                
                print(f"✅ Download and Gemini upload completed: {filename} -> {gemini_file_id}")
                return filepath, gemini_file_id
                
    except Exception as e:
        print(f"❌ Download/upload failed for {url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download/upload video: {str(e)}")


async def upload_file_content_to_gemini(file_content: bytes, filename: str) -> str:
    """Upload file content to Gemini Files API and return file ID"""
    try:
        if USE_VERTEX_AI:
            # Vertex AI: Upload to Cloud Storage
            from google.cloud import storage
            storage_client = storage.Client(project=os.getenv("VERTEX_PROJECT_ID"))
            
            bucket = storage_client.bucket(storage_bucket_name)
            try:
                bucket.reload()
            except Exception:
                bucket = storage_client.create_bucket(storage_bucket_name, location=os.getenv("VERTEX_LOCATION", "europe-west1"))
                
            # Generate unique blob name
            file_id = str(uuid.uuid4())
            file_extension = os.path.splitext(filename)[1] if filename else ""
            blob_name = f"stock_videos/{file_id}{file_extension}"
            
            # Upload to Cloud Storage
            blob = bucket.blob(blob_name)
            blob.upload_from_string(file_content, content_type="video/mp4")
            
            gs_uri = f"gs://{storage_bucket_name}/{blob_name}"
            return gs_uri
            
        else:
            # Standard Gemini API: Use Files API
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}") as tmp_file:
                tmp_file.write(file_content)
                tmp_file.flush()
                
                # Upload to Gemini Files API
                uploaded_file = gemini_api.files.upload(file=tmp_file.name)
                
                # Clean up temporary file
                os.unlink(tmp_file.name)
                
                # Wait for file to be ready
                import time
                max_wait_time = 30
                wait_interval = 2
                elapsed_time = 0
                
                while elapsed_time < max_wait_time:
                    try:
                        file_status = gemini_api.files.get(name=uploaded_file.name)
                        if hasattr(file_status, 'state') and file_status.state == 'ACTIVE':
                            break
                        else:
                            time.sleep(wait_interval)
                            elapsed_time += wait_interval
                    except Exception as e:
                        time.sleep(wait_interval)
                        elapsed_time += wait_interval
                
                return uploaded_file.name
                
    except Exception as e:
        print(f"❌ Gemini upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload to Gemini: {str(e)}")


async def upload_file_content_to_gemini(file_content: bytes, filename: str) -> str:
    """Upload file content to Gemini Files API and return file ID"""
    try:
        if USE_VERTEX_AI:
            # Vertex AI: Upload to Cloud Storage
            from google.cloud import storage
            storage_client = storage.Client(project=os.getenv("VERTEX_PROJECT_ID"))
            
            bucket = storage_client.bucket(storage_bucket_name)
            try:
                bucket.reload()
            except Exception:
                bucket = storage_client.create_bucket(storage_bucket_name, location=os.getenv("VERTEX_LOCATION", "europe-west1"))
                
            # Generate unique blob name
            file_id = str(uuid.uuid4())
            file_extension = os.path.splitext(filename)[1] if filename else ""
            blob_name = f"stock_videos/{file_id}{file_extension}"
            
            # Upload to Cloud Storage
            blob = bucket.blob(blob_name)
            blob.upload_from_string(file_content, content_type="video/mp4")
            
            gs_uri = f"gs://{storage_bucket_name}/{blob_name}"
            return gs_uri
            
        else:
            # Standard Gemini API: Use Files API
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}") as tmp_file:
                tmp_file.write(file_content)
                tmp_file.flush()
                
                # Upload to Gemini Files API
                uploaded_file = gemini_api.files.upload(file=tmp_file.name)
                
                # Clean up temporary file
                os.unlink(tmp_file.name)
                
                # Wait for file to be ready
                import time
                max_wait_time = 30
                wait_interval = 2
                elapsed_time = 0
                
                while elapsed_time < max_wait_time:
                    try:
                        file_status = gemini_api.files.get(name=uploaded_file.name)
                        if hasattr(file_status, 'state') and file_status.state == 'ACTIVE':
                            break
                        else:
                            time.sleep(wait_interval)
                            elapsed_time += wait_interval
                    except Exception as e:
                        time.sleep(wait_interval)
                        elapsed_time += wait_interval
                
                return uploaded_file.name
                
    except Exception as e:
        print(f"❌ Gemini upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload to Gemini: {str(e)}")


# AI Video Curation Function
async def curate_videos_with_ai(videos: List[Dict], query: str, max_count: int = 4) -> Dict:
    """
    Use Gemini Flash Lite to select the most relevant videos from Pexels data
    
    Args:
        videos: List of video metadata from Pexels API (with url, duration, etc.)
        query: User's search query 
        max_count: Maximum videos to return (0-4)
    
    Returns:
        {
            "selected": [1, 3, 7],  # Indices of selected videos (0-based)
            "explanation": "These videos best match ocean waves request..."
        }
    """
    if not videos:
        return {"selected": [], "explanation": "No videos provided for curation"}
    
    def extract_title_from_url(url):
        """Extract descriptive title from Pexels video URL slug"""
        import re
        match = re.search(r'/video/([^/]+)-\d+/?$', url)
        if match:
            slug = match.group(1)
            title = slug.replace('-', ' ').title()
            return title
        return "Unknown video"
    
    try:
        # Initialize Gemini client
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Format videos for AI analysis using URL slug extraction
        video_descriptions = []
        for i, video in enumerate(videos):
            url = video.get("url", "")
            extracted_title = extract_title_from_url(url)
            duration = video.get("duration", 0)
            width = video.get("width", 0)
            height = video.get("height", 0)
            quality = f"{width}x{height}" if width and height else "Unknown quality"
            
            video_descriptions.append(f"[{i}] \"{extracted_title}\" ({duration}s, {quality})")
        
        # Create curation prompt with extracted titles
        prompt = f"""You are a video curation expert. From the following {len(videos)} videos, select 0-{max_count} that are most relevant for: "{query}"

Guidelines:
- Only select videos that would genuinely help with this request
- Prioritize videos that closely match the visual/thematic intent
- Consider the extracted titles from video URLs as the main content indicator
- It's better to return fewer high-quality matches than many mediocre ones
- Return 0 videos if none are truly useful
- Consider video duration for practical usability (prefer 5-30 seconds for most use cases)

Videos to evaluate (extracted from URL slugs):
{chr(10).join(video_descriptions)}

Return JSON with only the selected video indices (0-based)."""

        # Configure for speed
        generation_config = types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json",
            response_schema=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "selected": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(type=types.Type.INTEGER)
                    )
                },
                required=["selected"]
            )
        )
        
        # Call Gemini Flash Lite
        response = client.models.generate_content(
            model="gemini-flash-lite-latest",  # Using the model you specified
            contents=prompt,
            config=generation_config
        )
        
        # Parse response
        result = json.loads(response.text)
        selected_indices = result.get("selected", [])
        
        # Validate indices
        valid_indices = [i for i in selected_indices if 0 <= i < len(videos)]
        
        # Limit to max_count
        final_indices = valid_indices[:max_count]
        
        print(f"🤖 AI Curation: Selected {len(final_indices)} videos from {len(videos)} for '{query}'")
        
        return {
            "selected": final_indices,
            "explanation": ""
        }
        
    except Exception as e:
        print(f"❌ AI curation failed: {str(e)}")
        # Fallback: return first min(max_count, len(videos)) videos
        fallback_count = min(max_count, len(videos))
        return {
            "selected": list(range(fallback_count)),
            "explanation": f"AI curation failed, returning first {fallback_count} videos"
        }


class Message(BaseModel):
    message: str  # the full user message


class ConversationMessage(BaseModel):
    user_request: str  # What the user asked for
    ai_response: str  # What the AI generated (explanation)
    generated_code: str  # The code that was generated
    timestamp: str  # When this interaction happened


class CompositionRequest(BaseModel):
    user_request: str  # User's description of what they want
    preview_settings: Dict[str, Any]  # Current preview settings (width, height, etc.)
    media_library: Optional[List[Dict[str, Any]]] = []  # Available media files in library
    current_composition: Optional[List[Dict[str, Any]]] = None  # Current composition blueprint for incremental editing
    conversation_history: Optional[List[ConversationMessage]] = []  # Past requests and responses for context
    preview_frame: Optional[str] = None  # Base64 encoded screenshot of current frame
    model_type: Optional[str] = "gemini"  # AI model to use: gemini, claude, vertex, openai (defaults to gemini)


class GeneratedComposition(BaseModel):
    tsx_code: str  # Raw Remotion TSX composition code
    explanation: str
    duration: float
    success: bool


class CompositionResponse(BaseModel):
    composition_code: str  # Generated Remotion composition TSX code
    content_data: List[Dict[str, Any]]  # For backwards compatibility (empty)
    explanation: str  # Human-readable explanation of what was generated
    duration: float  # Duration in seconds
    success: bool
    error_message: Optional[str] = None


class CodeFixRequest(BaseModel):
    broken_code: str  # The code that failed to execute
    error_message: str  # The exact error from frontend
    error_stack: Optional[str] = None  # Full error stack if available
    media_library: Optional[List[Dict[str, Any]]] = []  # Available media files


class CodeFixResponse(BaseModel):
    corrected_code: str  # Fixed code
    explanation: str  # What was fixed
    duration: float  # Updated duration
    success: bool
    error_message: Optional[str] = None


class GeminiUploadResponse(BaseModel):
    success: bool
    gemini_file_id: Optional[str] = None
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    error_message: Optional[str] = None


def is_youtube_url(url: str) -> bool:
    """Check if the URL is a YouTube URL."""
    youtube_domains = [
        'youtube.com', 'www.youtube.com', 'm.youtube.com',
        'youtu.be', 'www.youtu.be'
    ]
    return any(domain in url.lower() for domain in youtube_domains)


class VideoAnalysisRequest(BaseModel):
    file_url: str  # Can be YouTube URL or Gemini file ID (files/abc123)
    question: str


class VideoAnalysisResponse(BaseModel):
    success: bool
    analysis: Optional[str] = None
    error_message: Optional[str] = None


# NOTE: /upload-to-gemini endpoint removed - replaced by unified /upload-media endpoint
# Gemini can now access files directly from GCS using signed URLs
# Use /upload-media for all file uploads (supports JWT auth and user/session isolation)


@app.post("/ai/generate-composition")
async def generate_composition(request: CompositionRequest) -> CompositionResponse:
    """Generate a new Remotion composition blueprint using AI."""
    
    print(f"🎬 Main: Processing request: '{request.user_request}'")
    print(f"📝 Main: Current composition has {len(request.current_composition or [])} tracks")
    
    # AI Blueprint Generation (NEW SYSTEM)
    print(f"🚀 AI: Generating CompositionBlueprint with updated system")
    
    # Convert to dict format expected by code generator
    request_dict = {
        "user_request": request.user_request,
        "preview_settings": request.preview_settings,
        "media_library": request.media_library,
        "current_composition": request.current_composition,
        "conversation_history": request.conversation_history,
        "model_type": request.model_type
    }
    
    # Call the blueprint generation module (LLM-agnostic)
    result = await generate_composition_with_validation(request_dict)
    
    print(f"✅ Main: Blueprint generation completed - Success: {result['success']}")
    
    # Convert result back to the response model
    return CompositionResponse(
        composition_code=result["composition_code"],  # This is now CompositionBlueprint JSON
        content_data=result["content_data"],
        explanation=result["explanation"],
        duration=result["duration"],
        success=result["success"],
        error_message=result.get("error_message")
    )


@app.post("/ai/fix-code")
async def fix_code(request: CodeFixRequest) -> CodeFixResponse:
    """Fix broken AI-generated code based on real runtime errors from the frontend."""
    
    print(f"🔧 Fix: Processing error correction")
    print(f"🔧 Fix: Error message: {request.error_message}")
    
    try:
        # System instruction for code fixing
        system_instruction = """You are a world-class Remotion developer and code fixing specialist. Your job is to fix broken React/TypeScript code that failed during execution.

⚠️ **CRITICAL**: Only fix the specific error - do not redesign, rewrite, or improve the code. Make the minimal possible change to resolve the error.


**CRITICAL: EXECUTION CONTEXT:**
- Code executes in React.createElement environment with Function() constructor
- Use React.createElement syntax, not JSX
- Use 'div' elements for text (no Text component in Remotion)

RESPONSE FORMAT - You must respond with EXACTLY this structure:
DURATION: [number in seconds based on composition content and timing]
CODE:
[raw JavaScript code using React.createElement - no markdown blocks, no import statements]

Fix ONLY the error and return the corrected code that will execute properly."""

        # User prompt with just the error and broken code
        user_prompt = f"""Fix this broken code:

ERROR MESSAGE:
{request.error_message}

BROKEN CODE:
{request.broken_code}

Fix the error and return the corrected code."""

        # Create thinking config for code fixes
        thinking_config = types.ThinkingConfig(
            include_thoughts=True,
            thinking_budget=2000  # Default thinking budget for fixes
        )

        # Use the same AI call pattern as other endpoints
        response = gemini_api.models.generate_content(
            model="gemini-flash-latest",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.1,  # Low temperature for precise fixes
                max_output_tokens=4000,
                thinking_config=thinking_config
            ),
            contents=user_prompt
        )
        
        duration, corrected_code = code_generator.parse_ai_response(response.text)
        
        print(f"✅ Fix: Generated corrected code (duration: {duration}s)")
        
        return CodeFixResponse(
            corrected_code=corrected_code,
            explanation=f"Fixed error: {request.error_message[:100]}...",
            duration=duration,
            success=True
        )
        
    except Exception as e:
        print(f"❌ Fix: Error correction failed - {str(e)}")
        
        return CodeFixResponse(
            corrected_code=request.broken_code,  # Return original as fallback
            explanation=f"Error correction failed: {str(e)}",
            duration=10.0,
            success=False,
            error_message=str(e)
        )


@app.post("/analyze-video")
async def analyze_video(request: VideoAnalysisRequest) -> VideoAnalysisResponse:
    """Analyze a video file using Gemini - supports both YouTube URLs and uploaded file IDs."""
    
    try:
        print(f"🎬 Video Analysis: Analyzing {request.file_url}")
        print(f"🔍 Question: {request.question}")
        
        # Check if it's a YouTube URL
        if is_youtube_url(request.file_url):
            print(f"📺 Detected YouTube URL: {request.file_url}")
            
            # For YouTube URLs, use Gemini's direct URL support with correct structure
            response = gemini_api.models.generate_content(
                model="gemini-flash-latest",
                contents=types.Content(
                    parts=[
                        types.Part(
                            file_data=types.FileData(file_uri=request.file_url)
                        ),
                        types.Part(text=request.question)
                    ]
                ),
                config=types.GenerateContentConfig(temperature=0.1)
            )
        elif USE_VERTEX_AI:
            # For Vertex AI, the file_url is actually a Cloud Storage URI
            # Use a simpler approach - pass the file URI directly in contents
            response = gemini_api.models.generate_content(
                model="gemini-flash-latest",
                contents=[request.file_url, request.question],
                config=types.GenerateContentConfig(temperature=0.1)
            )
        else:
            # For regular Gemini API, use the file reference directly
            # The file_url is the file URI from Files API (e.g., "files/abc123")
            # We need to get the file object from the file ID
            file_obj = gemini_api.files.get(name=request.file_url)
            
            # Check if file is ready for analysis
            if hasattr(file_obj, 'state') and file_obj.state != 'ACTIVE':
                raise Exception(f"Video file is not ready for analysis yet (state: {file_obj.state}). Please wait a moment and try again.")
            
            response = gemini_api.models.generate_content(
                model="gemini-flash-latest", 
                contents=[file_obj, request.question],
                config=types.GenerateContentConfig(temperature=0.1)
            )
        
        analysis_result = response.text
        print(f"✅ Video Analysis: Success - {len(analysis_result)} characters")
        
        return VideoAnalysisResponse(
            success=True,
            analysis=analysis_result
        )
        
    except Exception as e:
        print(f"❌ Video Analysis: Failed - {str(e)}")
        
        # Provide user-friendly error messages
        error_msg = str(e)
        if "API key" in error_msg.lower():
            user_error = "AI service authentication failed. Please check server configuration."
        elif "network" in error_msg.lower() or "connection" in error_msg.lower():
            user_error = "Network connection error. Please check your internet connection and try again."
        elif "quota" in error_msg.lower() or "limit" in error_msg.lower():
            user_error = "AI service quota exceeded. Please try again later."
        elif "not found" in error_msg.lower():
            user_error = "Video file not found. Please try uploading the video again."
        elif "failed_precondition" in error_msg.lower() or "not in an active state" in error_msg.lower():
            user_error = "Video is still being processed by the AI service. Please wait a moment and try again."
        elif "not ready for analysis yet" in error_msg.lower():
            user_error = "Video is still being processed. Please wait a moment and try again."
        else:
            user_error = f"Video analysis failed: {error_msg}"
        
        return VideoAnalysisResponse(
            success=False,
            error_message=user_error
        )


# Initialize content generation provider
content_generator = ContentGenerationProvider()

# Store active generation operations
active_operations = {}


@app.post("/generate-content", response_model=GenerateContentResponse)
async def generate_content(
    request: GenerateContentRequest,
    user: dict = Depends(get_current_user)
):
    """Generate video or image content using Gemini AI with GCS storage"""
    user_id = user.get("user_id")
    session_id = user.get("session_id")
    
    try:
        print(f"🎨 Generating {request.content_type} for user {user_id}, session {session_id}")
        print(f"📝 Prompt: '{request.prompt[:100]}...'")
        
        if request.content_type == "video":
            # Handle reference image if provided
            reference_image = None
            if request.reference_image:
                try:
                    # Decode base64 image
                    import base64
                    image_data = base64.b64decode(request.reference_image)
                    reference_image = Image.open(BytesIO(image_data))
                except Exception as e:
                    print(f"⚠️ Failed to process reference image: {e}")
            
            # Start video generation (async)
            operation = await content_generator.generate_video(
                prompt=request.prompt,
                negative_prompt=request.negative_prompt,
                aspect_ratio=request.aspect_ratio,
                resolution=request.resolution,
                reference_image=reference_image
            )
            
            # Poll internally until video generation is complete
            import time
            print("Video generation started, polling for completion...")
            while not operation.done:
                print("⏳ Video still generating, waiting 5 seconds...")
                time.sleep(5)
                operation = await content_generator.check_video_status(operation)
            
            print("Video generation completed!")
            
            # Process completed video (same logic as check_generation_status)
            try:
                # Download the generated video
                generated_video = operation.response.generated_videos[0]
                
                # Create unique filename
                asset_id = str(uuid.uuid4())
                file_name = f"generated_video_{asset_id}.mp4"
                
                # Download to temporary file
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
                    content_generator.api_client.files.download(file=generated_video.video)
                    generated_video.video.save(tmp_file.name)
                    
                    # Upload to GCS
                    with open(tmp_file.name, 'rb') as video_file:
                        gcs_url = upload_file_to_gcs(
                            file_data=video_file,
                            user_id=user_id,
                            session_id=session_id,
                            filename=file_name,
                            content_type="video/mp4"
                        )
                    
                    # Get file size before cleanup
                    file_size = os.path.getsize(tmp_file.name)
                    
                    # Cleanup temp file
                    os.unlink(tmp_file.name)
                
                print(f"☁️  Generated video uploaded to GCS: {gcs_url}")
                
                # Create asset response with GCS URL
                generated_asset = GeneratedAsset(
                    asset_id=asset_id,
                    content_type="video",
                    file_path=f"{user_id}/{session_id}/{file_name}",  # GCS path
                    file_url=gcs_url,  # GCS signed URL
                    prompt=request.prompt,
                    duration_seconds=8.0,  # Veo generates 8-second videos
                    width=1280 if request.resolution == "720p" else 1920,
                    height=720 if request.resolution == "720p" else 1080,
                    file_size=file_size
                )
                
                return GenerateContentResponse(
                    success=True,
                    generated_asset=generated_asset,
                    status="completed"
                )
                
            except Exception as e:
                print(f"❌ Failed to download generated video: {e}")
                return GenerateContentResponse(
                    success=False,
                    status="failed",
                    error_message=f"Failed to download video: {str(e)}"
                )
            
        elif request.content_type == "image":
            # Handle reference images if provided
            reference_images = []
            if request.reference_image:
                try:
                    import base64
                    image_data = base64.b64decode(request.reference_image)
                    reference_image = Image.open(BytesIO(image_data))
                    reference_images.append(reference_image)
                except Exception as e:
                    print(f"⚠️ Failed to process reference image: {e}")
            
            # Generate image (synchronous)
            response = await content_generator.generate_image(
                prompt=request.prompt,
                reference_images=reference_images
            )
            
            # Save generated image
            asset_id = str(uuid.uuid4())
            file_name = f"generated_image_{asset_id}.png"
            
            # Extract and save image from Imagen response
            if response.generated_images and len(response.generated_images) > 0:
                print(f"🎯 Found {len(response.generated_images)} generated images")
                generated_image = response.generated_images[0]
                
                # Get the PIL Image object from the Google GenAI Image object
                pil_image = generated_image.image._pil_image
                print(f"📸 PIL image size: {pil_image.size}")
                
                # Save to temporary file then upload to GCS
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                    pil_image.save(tmp_file.name)
                    
                    # Upload to GCS
                    with open(tmp_file.name, 'rb') as image_file:
                        gcs_url = upload_file_to_gcs(
                            file_data=image_file,
                            user_id=user_id,
                            session_id=session_id,
                            filename=file_name,
                            content_type="image/png"
                        )
                    
                    # Get file info before cleanup
                    width, height = pil_image.size
                    file_size = os.path.getsize(tmp_file.name)
                    
                    # Cleanup temp file
                    os.unlink(tmp_file.name)
                
                print(f"☁️  Generated image uploaded to GCS: {gcs_url}")
                print(f"📏 Image dimensions: {width}x{height}, file size: {file_size} bytes")
                
                # Create asset response with GCS URL
                generated_asset = GeneratedAsset(
                    asset_id=asset_id,
                    content_type="image",
                    file_path=f"{user_id}/{session_id}/{file_name}",  # GCS path
                    file_url=gcs_url,  # GCS signed URL
                    prompt=request.prompt,
                    width=width,
                    height=height,
                    file_size=file_size
                )
                
                return GenerateContentResponse(
                    success=True,
                    generated_asset=generated_asset,
                    status="completed"
                )
            
            raise HTTPException(status_code=500, detail="No image generated in response")
        
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported content type: {request.content_type}")
            
    except Exception as e:
        print(f"❌ Content generation failed: {str(e)}")
        return GenerateContentResponse(
            success=False,
            status="failed",
            error_message=str(e)
        )


@app.post("/check-generation-status", response_model=CheckGenerationStatusResponse)
async def check_generation_status(
    request: CheckGenerationStatusRequest,
    user: dict = Depends(get_current_user)
):
    """Check status of video generation operation with GCS storage"""
    user_id = user.get("user_id")
    session_id = user.get("session_id")
    
    try:
        operation_id = request.operation_id
        
        if operation_id not in active_operations:
            raise HTTPException(status_code=404, detail="Operation not found")
        
        operation_data = active_operations[operation_id]
        operation = operation_data['operation']
        stored_prompt = operation_data['prompt']
        stored_resolution = operation_data['resolution']
        
        # Check current status
        updated_operation = await content_generator.check_video_status(operation)
        
        if updated_operation.done:
            # Generation completed
            try:
                # Download the generated video
                generated_video = updated_operation.response.generated_videos[0]
                
                # Create unique filename
                asset_id = str(uuid.uuid4())
                file_name = f"generated_video_{asset_id}.mp4"
                
                # Download to temporary file
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
                    content_generator.api_client.files.download(file=generated_video.video)
                    generated_video.video.save(tmp_file.name)
                    
                    # Upload to GCS
                    with open(tmp_file.name, 'rb') as video_file:
                        gcs_url = upload_file_to_gcs(
                            file_data=video_file,
                            user_id=user_id,
                            session_id=session_id,
                            filename=file_name,
                            content_type="video/mp4"
                        )
                    
                    # Get file size before cleanup
                    file_size = os.path.getsize(tmp_file.name)
                    
                    # Cleanup temp file
                    os.unlink(tmp_file.name)
                
                print(f"☁️  Generated video uploaded to GCS: {gcs_url}")
                
                # Create asset response with GCS URL
                generated_asset = GeneratedAsset(
                    asset_id=asset_id,
                    content_type="video",
                    file_path=f"{user_id}/{session_id}/{file_name}",  # GCS path
                    file_url=gcs_url,  # GCS signed URL
                    prompt=stored_prompt,  # Use stored prompt
                    duration_seconds=8.0,  # Veo generates 8-second videos
                    width=1280 if stored_resolution == "720p" else 1920,  # Use stored resolution
                    height=720 if stored_resolution == "720p" else 1080,
                    file_size=file_size
                )
                
                # Clean up operation
                del active_operations[operation_id]
                
                return CheckGenerationStatusResponse(
                    success=True,
                    status="completed",
                    generated_asset=generated_asset
                )
                
            except Exception as e:
                print(f"❌ Failed to download generated video: {e}")
                del active_operations[operation_id]
                return CheckGenerationStatusResponse(
                    success=False,
                    status="failed",
                    error_message=f"Failed to download video: {str(e)}"
                )
        else:
            # Still processing
            return CheckGenerationStatusResponse(
                success=True,
                status="processing"
            )
            
    except Exception as e:
        print(f"❌ Status check failed: {str(e)}")
        return CheckGenerationStatusResponse(
            success=False,
            status="failed", 
            error_message=str(e)
        )


@app.post("/fetch-stock-video", response_model=FetchStockVideoResponse)
async def fetch_stock_video(
    request: FetchStockVideoRequest,
    user: dict = Depends(get_current_user)
):
    """
    AI-Enhanced stock video fetch endpoint with intelligent curation and GCS storage:
    1. Search Pexels for 50 landscape videos (balanced for API limits)
    2. Use AI to curate and select 0-4 most relevant videos
    3. Upload selected videos directly to GCS with user/session isolation
    4. Return GCS URLs for frontend use
    5. No local storage - everything goes to cloud
    """
    user_id = user.get("user_id")
    session_id = user.get("session_id")
    
    print(f"🔍 Fetching stock videos for query: '{request.query}' with AI curation")
    print(f"👤 User: {user_id}, Session: {session_id}")
    
    try:
        # Step 1: Search Pexels for 50 videos (more variety for better AI curation)
        search_results = await search_pexels_videos(request.query, per_page=50)
        videos_data = search_results.get("videos", [])
        
        if not videos_data:
            raise HTTPException(status_code=404, detail="No videos found for query")
        
        print(f"📊 Found {len(videos_data)} videos from Pexels for AI analysis")
        
        # Step 2: Use AI to curate videos (select 0-4 most relevant)
        print(f"🤖 Running AI curation on {len(videos_data)} videos...")
        curation_result = await curate_videos_with_ai(videos_data, request.query, max_count=4)
        selected_indices = curation_result["selected"]
        curation_explanation = curation_result["explanation"]
        
        if not selected_indices:
            print(f"🚫 AI found no relevant videos for query: '{request.query}'")
            return FetchStockVideoResponse(
                success=True,
                query=request.query,
                videos=[],
                total_results=len(videos_data),
                ai_curation_explanation=curation_explanation
            )
        
        selected_videos = [videos_data[i] for i in selected_indices]
        print(f"✨ AI selected {len(selected_videos)} videos: {selected_indices}")
        print(f"🧠 AI reasoning: {curation_explanation}")
        
        # Step 3: Create shared HTTP client for all operations
        timeout = httpx.Timeout(60.0)
        async with httpx.AsyncClient(timeout=timeout) as shared_client:
            
            # Step 4: Process AI-selected videos in parallel - upload directly to GCS
            async def process_video(video, index):
                """Process a single video: upload HD quality to GCS"""
                video_files = video.get("video_files", [])
                
                # Select HIGH quality for frontend use
                best_file = select_best_video_file(video_files)
                
                if not best_file:
                    raise Exception("No suitable video files found")
                
                # Generate filename
                asset_id = str(uuid.uuid4())
                file_name = f"stock_video_{asset_id}.mp4"
                
                print(f"📥 Processing AI-selected video {index+1}/{len(selected_videos)}:")
                print(f"  Quality: {best_file['quality']} {best_file.get('width')}x{best_file.get('height')}")
                print(f"  Source: {best_file['link']}")
                
                # Upload directly to GCS from Pexels URL (run in thread pool)
                try:
                    # Run sync GCS function in thread pool to avoid blocking
                    loop = asyncio.get_event_loop()
                    gcs_url = await loop.run_in_executor(
                        None,
                        upload_url_to_gcs,
                        best_file["link"],
                        user_id,
                        session_id,
                        file_name
                    )
                    print(f"☁️  Uploaded to GCS: {gcs_url}")
                except Exception as e:
                    print(f"❌ GCS upload failed: {e}")
                    raise Exception(f"Failed to upload to GCS: {e}")
                
                # Create stock result with GCS URL
                stock_result = StockVideoResult(
                    id=video["id"],
                    pexels_url=video.get("url", ""),
                    download_url=gcs_url,
                    preview_image=video.get("image", ""),
                    duration=video.get("duration", 0),
                    width=best_file.get("width", video.get("width", 0)),
                    height=best_file.get("height", video.get("height", 0)),
                    file_type=best_file.get("file_type", "video/mp4"),
                    quality=best_file.get("quality", "sd") or "sd",  # Handle None quality
                    photographer=video.get("user", {}).get("name", "Unknown"),
                    photographer_url=video.get("user", {}).get("url", ""),
                    upload_status="uploaded",  # Already uploaded to GCS
                    gemini_file_id=None  # Gemini can access GCS URLs directly
                )
                
                print(f"✅ Completed AI-selected video {index+1}/{len(selected_videos)}: {file_name} → GCS")
                return stock_result
            
            # Process all AI-selected videos in parallel with shared client
            tasks = [
                asyncio.create_task(process_video(video, i)) 
                for i, video in enumerate(selected_videos)
            ]
            
            # Wait for all AI-selected videos to complete (with error handling)
            stock_results = []
            completed_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(completed_results):
                if isinstance(result, Exception):
                    print(f"❌ Failed to process AI-selected video {i+1}/{len(selected_videos)}: {result}")
                    continue  # Skip failed videos, don't add to results
                else:
                    stock_results.append(result)
            
            if not stock_results:
                raise HTTPException(status_code=500, detail="Failed to process any AI-selected videos")
            
            print(f"🎉 Successfully processed {len(stock_results)}/{len(selected_videos)} AI-curated videos")
            
            return FetchStockVideoResponse(
                success=True,
                query=request.query,
                videos=stock_results,
                total_results=len(videos_data),
                ai_curation_explanation=curation_explanation
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Stock video fetch error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch stock videos: {str(e)}")


class ChatLogRequest(BaseModel):
    session_id: str
    log_entry: Dict[str, Any]

@app.post("/chat/log")
async def save_chat_log(request: ChatLogRequest):
    """Save chat workflow log entries to files"""
    try:
        logs_dir = "logs"
        os.makedirs(logs_dir, exist_ok=True)
        
        log_file = os.path.join(logs_dir, f"chat_workflow_{request.session_id}.json")
        
        # Read existing log or create new one
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                log_data = json.load(f)
        else:
            log_data = {
                "session_id": request.session_id,
                "created": time.strftime("%Y-%m-%d %H:%M:%S"),
                "entries": []
            }
        
        # Append new entry
        log_data["entries"].append(request.log_entry)
        log_data["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
        log_data["total_entries"] = len(log_data["entries"])
        
        # Save updated log
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        return {"success": True, "log_file": log_file, "entry_count": len(log_data["entries"])}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save chat log: {str(e)}")


@app.get("/auth/test")
async def test_auth(user: dict = Depends(get_current_user)):
    """
    Test endpoint to verify JWT authentication is working.
    Requires valid Bearer token in Authorization header.
    """
    return {
        "success": True,
        "message": "Authentication successful!",
        "user": user
    }


@app.get("/health")
async def health_check():
    """Public health check endpoint (no auth required)"""
    return {"status": "healthy", "service": "screenwrite-backend"}


if __name__ == "__main__":
    import uvicorn

    # Run with extended timeout to handle long video generation (up to 10 minutes)
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=8001,
        timeout_keep_alive=600,  # 10 minutes for long video generation
        timeout_graceful_shutdown=30
    )
