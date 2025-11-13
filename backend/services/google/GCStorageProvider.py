"""Google Cloud Storage implementation of StorageProvider."""

import os
import uuid
import logging
import time
from typing import BinaryIO, Optional, List, Dict, Any
from datetime import datetime
from google.cloud import storage
from google.cloud.exceptions import NotFound, Conflict
import httpx
import asyncio
from functools import wraps

from services.base.StorageProvider import StorageProvider, StorageFile, UploadResult

logger = logging.getLogger(__name__)


def async_wrap(func):
    """Decorator to run sync GCS operations in executor."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
    return wrapper


class GCStorageProvider(StorageProvider):
    """
    Google Cloud Storage implementation.
    
    Features:
    - User/session isolation
    - Signed URL generation
    - Direct streaming from URLs
    - CORS configuration
    - Caching and optimization
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        bucket_name: Optional[str] = None,
        location: str = "us-central1",
        signed_url_expiration_days: int = 7,
        credentials_path: Optional[str] = None
    ):
        """
        Initialize GCS storage provider.
        
        Args:
            project_id: GCP project ID (uses default if not provided)
            bucket_name: GCS bucket name (from env or default)
            location: GCS bucket location
            signed_url_expiration_days: Default expiration for signed URLs
            credentials_path: Path to service account JSON (uses ADC if not provided)
        """
        self.project_id = project_id
        self.bucket_name = bucket_name or os.getenv("GCS_BUCKET_NAME", "screenwrite-media")
        self.location = location
        self.signed_url_expiration_days = signed_url_expiration_days
        
        # Initialize GCS client
        if credentials_path and os.path.exists(credentials_path):
            self.client = storage.Client.from_service_account_json(
                credentials_path,
                project=project_id
            )
            logger.info(f"GCS client initialized with service account from {credentials_path}")
        else:
            self.client = storage.Client(project=project_id)
            logger.info("GCS client initialized with Application Default Credentials")
        
        # Cache bucket after first access
        self._bucket_cache: Optional[storage.Bucket] = None
        
        logger.info(f"GCStorageProvider initialized: bucket={self.bucket_name}, location={self.location}")
    
    def _get_or_create_bucket(self) -> storage.Bucket:
        """Get or create bucket with CORS configuration (synchronous)."""
        if self._bucket_cache is not None:
            return self._bucket_cache
        
        try:
            bucket = self.client.get_bucket(self.bucket_name)
            
            # Check and configure CORS if needed
            current_cors = bucket.cors
            needs_cors_update = True
            
            if current_cors:
                for rule in current_cors:
                    if "*" in rule.get("origin", []) and "GET" in rule.get("method", []):
                        needs_cors_update = False
                        break
            
            if needs_cors_update:
                bucket.cors = [
                    {
                        "origin": ["*"],
                        "method": ["GET", "HEAD"],
                        "responseHeader": ["Content-Type", "Range", "Accept-Ranges"],
                        "maxAgeSeconds": 3600
                    }
                ]
                bucket.patch()
                logger.info(f"CORS configured for bucket '{self.bucket_name}'")
            
            logger.info(f"Using existing bucket '{self.bucket_name}'")
            self._bucket_cache = bucket
            return bucket
            
        except NotFound:
            logger.info(f"Creating bucket '{self.bucket_name}'...")
            try:
                bucket = self.client.create_bucket(
                    self.bucket_name,
                    location=self.location
                )
                
                # Enable uniform bucket-level access
                bucket.iam_configuration.uniform_bucket_level_access_enabled = True
                bucket.patch()
                
                # Configure CORS
                bucket.cors = [
                    {
                        "origin": ["*"],
                        "method": ["GET", "HEAD"],
                        "responseHeader": ["Content-Type", "Range", "Accept-Ranges"],
                        "maxAgeSeconds": 3600
                    }
                ]
                bucket.patch()
                
                logger.info(f"Bucket '{self.bucket_name}' created successfully")
                self._bucket_cache = bucket
                return bucket
                
            except Conflict:
                # Race condition: bucket created by another process
                bucket = self.client.get_bucket(self.bucket_name)
                logger.info(f"Bucket '{self.bucket_name}' created by another process")
                self._bucket_cache = bucket
                return bucket
    
    def _generate_blob_path(self, user_id: str, session_id: str, filename: str) -> tuple[str, str]:
        """
        Generate unique blob path with UUID and sanitized filename.
        
        Returns:
            tuple: (full_blob_path, sanitized_filename)
        """
        import re
        from pathlib import Path
        
        file_uuid = str(uuid.uuid4())
        
        # Extract extension
        file_path = Path(filename)
        extension = file_path.suffix  # includes the dot, e.g., ".mp4"
        name_without_ext = file_path.stem
        
        # Sanitize the filename: replace special characters with underscores
        # Allow only alphanumeric, hyphens, underscores
        sanitized_name = re.sub(r'[^a-zA-Z0-9_-]', '_', name_without_ext)
        
        # Remove consecutive underscores
        sanitized_name = re.sub(r'_+', '_', sanitized_name)
        
        # Remove leading/trailing underscores
        sanitized_name = sanitized_name.strip('_')
        
        # If name is empty after sanitization, use 'file'
        if not sanitized_name:
            sanitized_name = 'file'
        
        # Construct final filename: uuid_sanitizedname.ext
        sanitized_filename = f"{sanitized_name}{extension}"
        full_blob_path = f"{user_id}/{session_id}/{file_uuid}_{sanitized_filename}"
        
        return full_blob_path, sanitized_filename

    
    async def upload_file(
        self,
        file_data: BinaryIO,
        user_id: str,
        session_id: str,
        filename: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> UploadResult:
        """Upload file from binary stream."""
        def _sync_upload():
            bucket = self._get_or_create_bucket()
            blob_path, sanitized_filename = self._generate_blob_path(user_id, session_id, filename)
            blob = bucket.blob(blob_path)
            
            if content_type:
                blob.content_type = content_type
            
            blob.cache_control = "public, max-age=31536000"
            
            if metadata:
                blob.metadata = metadata
            
            # Upload with automatic retry
            blob.upload_from_file(file_data, rewind=True)
            
            logger.info(f"File uploaded: {blob_path}")
            
            # Generate signed URL
            signed_url = blob.generate_signed_url(
                version="v4",
                expiration=self.signed_url_expiration_days * 24 * 60 * 60,
                method="GET"
            )
            
            public_url = blob.public_url
            size = blob.size or 0
            
            return UploadResult(
                path=blob_path,
                url=public_url,
                signed_url=signed_url,
                size=size,
                content_type=content_type,
                metadata=metadata,
                sanitized_filename=sanitized_filename
            )
        
        return await async_wrap(_sync_upload)()
    
    async def upload_from_url(
        self,
        url: str,
        user_id: str,
        session_id: str,
        filename: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> UploadResult:
        """Download from URL and upload to GCS (streaming) - fully async."""
        start_time = time.time()
        
        # Extract filename from URL if not provided
        if not filename:
            extracted = url.split('/')[-1].split('?')[0]
            final_filename = extracted if extracted else f"downloaded_{uuid.uuid4()}"
        else:
            final_filename = filename
        
        # Get bucket (sync operation wrapped in executor)
        loop = asyncio.get_event_loop()
        bucket = await loop.run_in_executor(None, self._get_or_create_bucket)
        
        blob_path, sanitized_filename = self._generate_blob_path(user_id, session_id, final_filename)
        blob = bucket.blob(blob_path)
        
        logger.info(f"Streaming from URL to GCS: {url} -> {blob_path}")
        
        # Stream directly from URL to GCS using async HTTP
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream('GET', url) as response:
                response.raise_for_status()
                
                content_type = response.headers.get('Content-Type')
                if content_type:
                    blob.content_type = content_type
                
                blob.cache_control = "public, max-age=31536000"
                
                if metadata:
                    blob.metadata = metadata
                
                content_length = response.headers.get('Content-Length')
                content_length_int = int(content_length) if content_length else None
                
                if content_length_int:
                    file_size_mb = content_length_int / 1024 / 1024
                    logger.info(f"File size: {file_size_mb:.2f} MB")
                
                # Read content and upload to GCS
                content = await response.aread()
                
                # Upload from bytes (GCS SDK is sync, but we've minimized blocking by using async HTTP)
                await loop.run_in_executor(
                    None,
                    lambda: blob.upload_from_string(content, content_type=content_type)
                )
        
        total_time = time.time() - start_time
        logger.info(f"Upload completed in {total_time:.2f}s")
        
        # Generate signed URL (sync operation wrapped)
        signed_url = await loop.run_in_executor(
            None,
            lambda: blob.generate_signed_url(
                version="v4",
                expiration=self.signed_url_expiration_days * 24 * 60 * 60,
                method="GET"
            )
        )
        
        public_url = blob.public_url
        size = blob.size or 0
        
        return UploadResult(
            path=blob_path,
            url=public_url,
            signed_url=signed_url,
            size=size,
            content_type=content_type,
            metadata=metadata,
            sanitized_filename=sanitized_filename
        )
    
    async def download_file(self, path: str, **kwargs) -> bytes:
        """Download file content as bytes."""
        def _sync_download():
            bucket = self._get_or_create_bucket()
            blob = bucket.blob(path)
            
            if not blob.exists():
                raise FileNotFoundError(f"File not found: {path}")
            
            return blob.download_as_bytes()
        
        return await async_wrap(_sync_download)()
    
    async def delete_file(self, path: str, **kwargs) -> bool:
        """Delete a file from GCS."""
        def _sync_delete():
            try:
                bucket = self._get_or_create_bucket()
                blob = bucket.blob(path)
                blob.delete()
                logger.info(f"File deleted: {path}")
                return True
            except NotFound:
                logger.warning(f"File not found for deletion: {path}")
                return False
        
        return await async_wrap(_sync_delete)()
    
    async def file_exists(self, path: str, **kwargs) -> bool:
        """Check if file exists."""
        def _sync_exists():
            bucket = self._get_or_create_bucket()
            blob = bucket.blob(path)
            return blob.exists()
        
        return await async_wrap(_sync_exists)()
    
    async def list_files(
        self,
        prefix: str,
        limit: Optional[int] = None,
        **kwargs
    ) -> List[StorageFile]:
        """List files with given prefix."""
        def _sync_list():
            bucket = self._get_or_create_bucket()
            blobs = bucket.list_blobs(prefix=prefix, max_results=limit)
            
            files = []
            for blob in blobs:
                files.append(StorageFile(
                    path=blob.name,
                    name=blob.name.split('/')[-1],
                    size=blob.size or 0,
                    content_type=blob.content_type,
                    created_at=blob.time_created,
                    updated_at=blob.updated,
                    metadata=blob.metadata
                ))
            
            return files
        
        return await async_wrap(_sync_list)()
    
    async def generate_signed_url(
        self,
        path: str,
        expiration_seconds: int = 604800,
        **kwargs
    ) -> str:
        """Generate signed URL for temporary access."""
        def _sync_generate_signed_url():
            bucket = self._get_or_create_bucket()
            blob = bucket.blob(path)
            
            return blob.generate_signed_url(
                version="v4",
                expiration=expiration_seconds,
                method="GET"
            )
        
        return await async_wrap(_sync_generate_signed_url)()
    
    async def get_public_url(self, path: str, **kwargs) -> str:
        """Get public URL for a file."""
        def _sync_get_public_url():
            bucket = self._get_or_create_bucket()
            blob = bucket.blob(path)
            return blob.public_url
        
        return await async_wrap(_sync_get_public_url)()
