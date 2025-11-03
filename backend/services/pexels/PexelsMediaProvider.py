"""Pexels implementation using their REST API with AI curation via Gemini."""

import json
import logging
import os
import uuid
from typing import List, Dict, Any, Optional
import httpx
from google.cloud import storage

from services.base.MediaProvider import (
    MediaProvider,
    MediaSearchRequest,
    MediaSearchResponse,
    MediaDownloadRequest,
    MediaItem,
    CuratedMediaItem,
    VideoFile,
    MediaCreator,
    MediaType,
    VideoOrientation
)
from services.base.ChatProvider import ChatMessage
from services.google.GeminiChatProvider import GeminiChatProvider

logger = logging.getLogger(__name__)


class PexelsMediaProvider(MediaProvider):
    """Pexels implementation using REST API with AI curation.
    
    Features:
    - Search for videos and images
    - AI-powered relevance ranking using Gemini
    - Native GCS upload support
    - Streaming downloads for efficiency
    
    Authentication is via PEXELS_API_KEY environment variable.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        gcs_bucket: Optional[str] = None,
        gemini_provider: Optional[GeminiChatProvider] = None
    ):
        """
        Initialize Pexels provider.
        
        Args:
            api_key: Pexels API key (optional, will use PEXELS_API_KEY env var if not provided)
            gcs_bucket: Default GCS bucket for uploads (optional, will use STOCK_MEDIA_BUCKET env var)
            gemini_provider: GeminiChatProvider instance for AI curation (optional, will create if not provided)
        """
        self.api_key = (api_key or os.getenv('PEXELS_API_KEY', '')).strip('"\'')
        if not self.api_key:
            raise ValueError("Pexels API key is required. Set PEXELS_API_KEY environment variable.")
        
        self.gcs_bucket = gcs_bucket or os.getenv('STOCK_MEDIA_BUCKET', 'screenwrite-stock-media')
        self.base_url = "https://api.pexels.com"
        
        # Initialize Gemini provider for AI curation (use Flash Lite for fast curation)
        self.gemini = gemini_provider or GeminiChatProvider(
            default_model_name="gemini-2.5-flash-lite",
            default_temperature=0.1,
            default_thinking_budget=0
        )
        
        # Initialize GCS client
        self.storage_client = storage.Client()
        
        logger.info(f"Initialized Pexels provider with GCS bucket: {self.gcs_bucket}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers for Pexels API."""
        return {"Authorization": self.api_key}
    
    def _extract_title_from_url(self, url: str) -> str:
        """Extract descriptive title from Pexels URL slug."""
        import re
        match = re.search(r'/(?:video|photo)/([^/]+)-\d+/?$', url)
        if match:
            slug = match.group(1)
            title = slug.replace('-', ' ').title()
            return title
        return "Unknown"
    
    def _parse_video_item(self, video_data: Dict[str, Any]) -> MediaItem:
        """Parse Pexels video data into MediaItem."""
        video_files = []
        for vf in video_data.get("video_files", []):
            video_files.append(VideoFile(
                id=vf.get("id", 0),
                quality=vf.get("quality", "sd"),
                file_type=vf.get("file_type", "video/mp4"),
                width=vf.get("width", 0),
                height=vf.get("height", 0),
                fps=vf.get("fps"),
                link=vf.get("link", ""),
                size_bytes=vf.get("size")
            ))
        
        user_data = video_data.get("user", {})
        creator = MediaCreator(
            id=user_data.get("id", 0),
            name=user_data.get("name", "Unknown"),
            url=user_data.get("url", "")
        )
        
        return MediaItem(
            id=video_data.get("id", 0),
            media_type=MediaType.VIDEO,
            url=video_data.get("url", ""),
            width=video_data.get("width", 0),
            height=video_data.get("height", 0),
            duration=video_data.get("duration", 0),
            preview_url=video_data.get("image", ""),
            creator=creator,
            video_files=video_files,
            avg_color=video_data.get("avg_color"),
            metadata=video_data
        )
    
    def _parse_image_item(self, image_data: Dict[str, Any]) -> MediaItem:
        """Parse Pexels image data into MediaItem."""
        user_data = image_data.get("photographer_user", {})
        creator = MediaCreator(
            id=user_data.get("id", 0),
            name=image_data.get("photographer", "Unknown"),
            url=image_data.get("photographer_url", "")
        )
        
        src = image_data.get("src", {})
        
        return MediaItem(
            id=image_data.get("id", 0),
            media_type=MediaType.IMAGE,
            url=image_data.get("url", ""),
            width=image_data.get("width", 0),
            height=image_data.get("height", 0),
            preview_url=src.get("medium", ""),
            download_url=src.get("original", ""),
            creator=creator,
            alt_text=image_data.get("alt", ""),
            avg_color=image_data.get("avg_color"),
            metadata=image_data
        )
    
    def _select_best_video_file(self, video_files: List[VideoFile]) -> Optional[VideoFile]:
        """Select the best quality video file for download."""
        if not video_files:
            return None
        
        # Priority: HD MP4 > SD MP4 > others
        hd_mp4 = [f for f in video_files if f.quality == "hd" and f.file_type == "video/mp4"]
        if hd_mp4:
            # Prefer 1920x1080 or 1280x720
            preferred = [f for f in hd_mp4 if f.width in [1920, 1280]]
            return preferred[0] if preferred else hd_mp4[0]
        
        sd_mp4 = [f for f in video_files if f.quality == "sd" and f.file_type == "video/mp4"]
        return sd_mp4[0] if sd_mp4 else video_files[0]
    
    async def search_media(
        self,
        request: MediaSearchRequest,
        **kwargs
    ) -> MediaSearchResponse:
        """
        Search Pexels for media items.
        
        Args:
            request: MediaSearchRequest with search parameters
            **kwargs: Additional Pexels API parameters
            
        Returns:
            MediaSearchResponse with found media items
        """
        if request.media_type == MediaType.VIDEO:
            endpoint = f"{self.base_url}/videos/search"
        elif request.media_type == MediaType.IMAGE:
            endpoint = f"{self.base_url}/v1/search"
        else:
            raise ValueError(f"Unsupported media type: {request.media_type}")
        
        params = {
            "query": request.query,
            "per_page": request.per_page,
            "page": request.page
        }
        
        if request.orientation:
            params["orientation"] = request.orientation.value
        
        if request.size:
            params["size"] = request.size
        
        if request.locale:
            params["locale"] = request.locale
        
        # Add any additional kwargs
        params.update(kwargs)
        
        logger.info(f"Searching Pexels for {request.media_type.value}: '{request.query}'")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    endpoint,
                    headers=self._get_headers(),
                    params=params
                )
            response.raise_for_status()
            data = response.json()
            
            # Parse media items
            media_items = []
            if request.media_type == MediaType.VIDEO:
                for video in data.get("videos", []):
                    media_items.append(self._parse_video_item(video))
            elif request.media_type == MediaType.IMAGE:
                for photo in data.get("photos", []):
                    media_items.append(self._parse_image_item(photo))
            
            total_results = data.get("total_results", 0)
            
            logger.info(f"Found {len(media_items)} {request.media_type.value}s (total: {total_results})")
            
            return MediaSearchResponse(
                query=request.query,
                media_items=media_items,
                total_results=total_results,
                page=request.page,
                per_page=request.per_page,
                provider="pexels",
                metadata=data
            )
            
        except httpx.HTTPStatusError as e:
            error_msg = f"Pexels API error: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        except httpx.RequestError as e:
            error_msg = f"Pexels request error: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    async def search_and_curate(
        self,
        request: MediaSearchRequest,
        max_curated: int = 3,
        **kwargs
    ) -> MediaSearchResponse:
        """
        Search Pexels and use AI to curate the most relevant results.
        
        This method:
        1. Searches Pexels for a larger set of results (default 50)
        2. Uses Gemini to select the most relevant items
        3. Returns a curated list
        
        Args:
            request: MediaSearchRequest with search parameters
            max_curated: Maximum number of items to curate (0-N)
            **kwargs: Additional parameters
            
        Returns:
            MediaSearchResponse with AI-curated media items
        """
        # Search with larger per_page for better curation options
        search_request = MediaSearchRequest(
            query=request.query,
            media_type=request.media_type,
            per_page=50,  # Get more results for AI to choose from
            page=request.page,
            orientation=request.orientation,
            size=request.size,
            locale=request.locale,
            metadata=request.metadata
        )
        
        # Perform search
        search_response = await self.search_media(search_request, **kwargs)
        
        if not search_response.media_items:
            logger.warning(f"No media found for query: '{request.query}'")
            return search_response
        
        logger.info(f"Curating {len(search_response.media_items)} items with AI (max: {max_curated})")
        
        # Prepare media descriptions for AI
        media_descriptions = []
        for i, item in enumerate(search_response.media_items):
            extracted_title = self._extract_title_from_url(item.url)
            
            if item.media_type == MediaType.VIDEO:
                quality = f"{item.width}x{item.height}" if item.width and item.height else "Unknown quality"
                desc = f"[{i}] \"{extracted_title}\" ({item.duration}s, {quality})"
            else:
                desc = f"[{i}] \"{extracted_title}\" ({item.width}x{item.height})"
            
            media_descriptions.append(desc)
        
        # Create curation prompt
        media_type_name = request.media_type.value
        prompt = f"""You are a {media_type_name} curation expert. From the following {len(search_response.media_items)} {media_type_name}s, select AT MOST {max_curated} that are most relevant for: "{request.query}"

Guidelines:
- Only select {media_type_name}s that would genuinely help with this request
- Prioritize items that closely match the visual/thematic intent
- Consider the extracted titles from URLs as the main content indicator
- It's better to return fewer high-quality matches than many mediocre ones
- Return 0 {media_type_name}s if none are truly useful
- MAXIMUM {max_curated} results - do not exceed this limit"""

        if request.media_type == MediaType.VIDEO:
            prompt += "\n- Consider video duration for practical usability (prefer 5-30 seconds for most use cases)"
        
        prompt += f"""

{media_type_name.capitalize()}s to evaluate (extracted from URL slugs):
{chr(10).join(media_descriptions)}

Return JSON with only the selected {media_type_name} indices (0-based) and a brief explanation."""
        
        # Call Gemini for curation
        try:
            messages = [ChatMessage(role="user", content=prompt)]
            
            schema = {
                "type": "object",
                "properties": {
                    "selected": {
                        "type": "array",
                        "items": {"type": "integer"}
                    },
                    "explanation": {"type": "string"}
                },
                "required": ["selected", "explanation"]
            }
            
            response = await self.gemini.generate_chat_response_with_schema(
                messages=messages,
                response_schema=schema,
                temperature=0.1,
                thinking_budget=0
            )
            
            selected_indices = response.get("selected", [])
            explanation = response.get("explanation", "")
            
            # Validate and limit indices
            valid_indices = [i for i in selected_indices if 0 <= i < len(search_response.media_items)]
            final_indices = valid_indices[:max_curated]
            
            logger.info(f"AI selected {len(final_indices)} {media_type_name}s: {final_indices}")
            logger.info(f"AI reasoning: {explanation}")
            
            # Create curated items list
            curated_items = []
            for idx in final_indices:
                curated_items.append(CuratedMediaItem(
                    media_item=search_response.media_items[idx],
                    relevance_score=100 - (final_indices.index(idx) * 10),  # Simple scoring based on rank
                    relevance_reasoning=explanation
                ))
            
            search_response.curated_items = curated_items
            search_response.ai_curation_explanation = explanation
            
            return search_response
            
        except Exception as e:
            logger.error(f"AI curation failed: {str(e)}")
            # Fallback: return first N items
            fallback_count = min(max_curated, len(search_response.media_items))
            curated_items = []
            for i in range(fallback_count):
                curated_items.append(CuratedMediaItem(
                    media_item=search_response.media_items[i],
                    relevance_reasoning=f"AI curation failed, returning top {fallback_count} results"
                ))
            search_response.curated_items = curated_items
            search_response.ai_curation_explanation = f"AI curation failed: {str(e)}"
            return search_response
    
    async def download_media(
        self,
        request: MediaDownloadRequest,
        **kwargs
    ) -> CuratedMediaItem:
        """
        Download media and optionally upload to GCS.
        
        Args:
            request: MediaDownloadRequest with download/upload parameters
            **kwargs: Additional parameters
            
        Returns:
            CuratedMediaItem with download/upload information
        """
        media_item = request.media_item
        
        # Determine download URL
        if media_item.media_type == MediaType.VIDEO:
            if not media_item.video_files:
                raise ValueError("No video files available for download")
            
            # Select appropriate quality
            if request.quality_preference == "best":
                video_file = max(media_item.video_files, key=lambda f: f.width * f.height)
            elif request.quality_preference == "lowest":
                video_file = min(media_item.video_files, key=lambda f: f.width * f.height)
            else:
                video_file = self._select_best_video_file(media_item.video_files)
            
            if not video_file:
                raise ValueError("Could not select video file for download")
            
            download_url = video_file.link
            file_extension = ".mp4"
            
        elif media_item.media_type == MediaType.IMAGE:
            download_url = media_item.download_url
            if not download_url:
                raise ValueError("No download URL available for image")
            file_extension = ".jpg"
        else:
            raise ValueError(f"Unsupported media type: {media_item.media_type}")
        
        logger.info(f"Downloading {media_item.media_type.value} from: {download_url}")
        
        try:
            # Download media with streaming
            timeout = httpx.Timeout(120.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream('GET', download_url, follow_redirects=True) as response:
                    response.raise_for_status()
                    
                    # Read content
                    content = b""
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        content += chunk
                    
                    file_size = len(content)
                    logger.info(f"Downloaded {file_size} bytes")
                    
                    result = CuratedMediaItem(
                        media_item=media_item,
                        file_size_bytes=file_size
                    )
                    
                    # Upload to GCS if requested
                    if request.upload_to_gcs:
                        bucket_name = request.gcs_bucket or self.gcs_bucket
                        
                        # Generate unique filename
                        asset_id = str(uuid.uuid4())
                        file_name = f"{media_item.media_type.value}_{asset_id}{file_extension}"
                        
                        if request.gcs_path:
                            blob_name = f"{request.gcs_path}/{file_name}"
                        else:
                            blob_name = f"stock_media/{file_name}"
                        
                        logger.info(f"Uploading to GCS: gs://{bucket_name}/{blob_name}")
                        
                        bucket = self.storage_client.bucket(bucket_name)
                        blob = bucket.blob(blob_name)
                        
                        # Determine content type
                        if media_item.media_type == MediaType.VIDEO:
                            content_type = "video/mp4"
                        elif media_item.media_type == MediaType.IMAGE:
                            content_type = "image/jpeg"
                        else:
                            content_type = "application/octet-stream"
                        
                        blob.upload_from_string(content, content_type=content_type)
                        blob.make_public()
                        
                        result.gcs_uri = f"gs://{bucket_name}/{blob_name}"
                        result.gcs_public_url = blob.public_url
                        
                        logger.info(f"Upload complete: {result.gcs_public_url}")
                    
                    # Save locally if requested
                    elif request.local_path:
                        with open(request.local_path, 'wb') as f:
                            f.write(content)
                        result.local_path = request.local_path
                        logger.info(f"Saved to: {request.local_path}")
                    
                    return result
                    
        except Exception as e:
            error_msg = f"Download failed: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    async def get_media_details(
        self,
        media_id: str,
        media_type: MediaType,
        **kwargs
    ) -> MediaItem:
        """
        Get detailed information about a specific media item.
        
        Args:
            media_id: Pexels media ID
            media_type: Type of media (video or image)
            **kwargs: Additional parameters
            
        Returns:
            MediaItem with detailed information
        """
        if media_type == MediaType.VIDEO:
            endpoint = f"{self.base_url}/videos/videos/{media_id}"
        elif media_type == MediaType.IMAGE:
            endpoint = f"{self.base_url}/v1/photos/{media_id}"
        else:
            raise ValueError(f"Unsupported media type: {media_type}")
        
        logger.info(f"Fetching details for {media_type.value} ID: {media_id}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    endpoint,
                    headers=self._get_headers()
                )
            response.raise_for_status()
            data = response.json()
            
            if media_type == MediaType.VIDEO:
                return self._parse_video_item(data)
            else:
                return self._parse_image_item(data)
                
        except httpx.HTTPStatusError as e:
            error_msg = f"Pexels API error: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        except httpx.RequestError as e:
            error_msg = f"Pexels request error: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
