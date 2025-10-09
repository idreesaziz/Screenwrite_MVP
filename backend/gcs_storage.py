"""
Google Cloud Storage helper functions for Screenwrite.

This module provides utilities for:
- Uploading files to GCS with user/session isolation
- Downloading URLs and uploading to GCS
- Deleting files from GCS
- Managing GCS buckets
"""

import os
import uuid
import logging
import time
from typing import Optional, BinaryIO
from google.cloud import storage
from google.cloud.exceptions import NotFound, Conflict
import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "screenwrite-media")
GCS_LOCATION = os.getenv("GCS_LOCATION", "us-central1")
GCS_SIGNED_URL_EXPIRATION_DAYS = int(os.getenv("GCS_SIGNED_URL_EXPIRATION_DAYS", "7"))

# Global cached client and bucket (initialized on first use)
_gcs_client = None
_gcs_bucket = None


def get_gcs_client() -> storage.Client:
    """
    Initialize and return a GCS client using Application Default Credentials.
    Uses a cached client after first initialization for better performance.
    
    Returns:
        storage.Client: Authenticated GCS client
    """
    global _gcs_client
    
    if _gcs_client is None:
        try:
            _gcs_client = storage.Client()
            logger.info("GCS client initialized successfully (cached for reuse)")
        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {e}")
            raise
    
    return _gcs_client


def get_or_create_bucket(
    bucket_name: str = GCS_BUCKET_NAME,
    location: str = GCS_LOCATION
) -> storage.Bucket:
    """
    Get an existing bucket or create a new one with uniform bucket-level access.
    Uses a cached bucket after first initialization for better performance.
    
    Args:
        bucket_name: Name of the GCS bucket
        location: GCS bucket location (e.g., 'us-central1')
    
    Returns:
        storage.Bucket: The GCS bucket object
    """
    global _gcs_bucket
    
    # Return cached bucket if it matches the requested bucket name
    if _gcs_bucket is not None and _gcs_bucket.name == bucket_name:
        return _gcs_bucket
    
    client = get_gcs_client()
    
    try:
        bucket = client.get_bucket(bucket_name)
        logger.info(f"Bucket '{bucket_name}' already exists (cached for reuse)")
        _gcs_bucket = bucket
        return bucket
    except NotFound:
        logger.info(f"Bucket '{bucket_name}' not found, creating...")
        try:
            bucket = client.create_bucket(
                bucket_name,
                location=location
            )
            # Enable uniform bucket-level access (IAM only, no ACLs)
            bucket.iam_configuration.uniform_bucket_level_access_enabled = True
            bucket.patch()
            logger.info(f"Bucket '{bucket_name}' created with uniform access in {location}")
            _gcs_bucket = bucket
            return bucket
        except Conflict:
            # Race condition: bucket was created between check and create
            bucket = client.get_bucket(bucket_name)
            logger.info(f"Bucket '{bucket_name}' created by another process")
            _gcs_bucket = bucket
            return bucket
        except Exception as e:
            logger.error(f"Failed to create bucket '{bucket_name}': {e}")
            raise


def upload_file_to_gcs(
    file_data: BinaryIO,
    user_id: str,
    session_id: str,
    filename: str,
    content_type: Optional[str] = None,
    bucket_name: str = GCS_BUCKET_NAME
) -> str:
    """
    Upload a file to GCS with user/session isolation.
    
    File path structure: {user_id}/{session_id}/{uuid}_{filename}
    
    Args:
        file_data: File-like object opened in binary mode ('rb')
        user_id: User ID from JWT for isolation
        session_id: Session ID from JWT for isolation
        filename: Original filename
        content_type: MIME type of the file (e.g., 'video/mp4', 'image/png')
        bucket_name: GCS bucket name
    
    Returns:
        str: Public URL of the uploaded file
    
    Raises:
        Exception: If upload fails
    """
    try:
        bucket = get_or_create_bucket(bucket_name)
        
        # Generate unique filename with UUID to avoid collisions
        file_uuid = str(uuid.uuid4())
        blob_path = f"{user_id}/{session_id}/{file_uuid}_{filename}"
        
        blob = bucket.blob(blob_path)
        
        # Set content type if provided
        if content_type:
            blob.content_type = content_type
        
        # Upload file (uses crc32c checksum by default in v3.0+)
        blob.upload_from_file(file_data, rewind=True)
        
        logger.info(f"File uploaded successfully to: {blob_path}")
        
        # Generate signed URL with 7-day expiration
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=GCS_SIGNED_URL_EXPIRATION_DAYS * 24 * 60 * 60,  # Days to seconds
            method="GET"
        )
        
        logger.info(f"Generated signed URL (expires in {GCS_SIGNED_URL_EXPIRATION_DAYS} days)")
        return signed_url
        
    except Exception as e:
        logger.error(f"Failed to upload file to GCS: {e}")
        raise


def upload_url_to_gcs(
    url: str,
    user_id: str,
    session_id: str,
    filename: Optional[str] = None,
    bucket_name: str = GCS_BUCKET_NAME
) -> str:
    """
    Download a file from a URL and upload it to GCS.
    
    Useful for:
    - Stock videos from Pexels/Shutterstock
    - Generated content from external APIs
    
    Args:
        url: URL to download the file from
        user_id: User ID from JWT for isolation
        session_id: Session ID from JWT for isolation
        filename: Optional filename (will be extracted from URL if not provided)
        bucket_name: GCS bucket name
    
    Returns:
        str: Public URL of the uploaded file in GCS
    
    Raises:
        Exception: If download or upload fails
    """
    try:
        start_time = time.time()
        
        # Extract filename from URL if not provided
        if not filename:
            filename = url.split('/')[-1].split('?')[0]
            if not filename:
                filename = f"downloaded_{uuid.uuid4()}"
        
        # Setup GCS upload
        setup_start = time.time()
        bucket = get_or_create_bucket(bucket_name)
        file_uuid = str(uuid.uuid4())
        blob_path = f"{user_id}/{session_id}/{file_uuid}_{filename}"
        blob = bucket.blob(blob_path)
        setup_time = time.time() - setup_start
        
        logger.info(f"GCS setup: {setup_time:.2f}s")
        logger.info(f"Streaming from URL to GCS: {url} -> {blob_path}")
        
        # Stream directly from URL to GCS using requests with chunked transfer
        download_start = time.time()
        with requests.get(url, stream=True, timeout=60) as response:
            response.raise_for_status()
            download_time = time.time() - download_start
            
            # Set content type from response headers
            content_type = response.headers.get('Content-Type')
            if content_type:
                blob.content_type = content_type
            
            # Get content length for progress tracking (optional)
            content_length = response.headers.get('Content-Length')
            content_length_int = None
            file_size_mb = 0
            if content_length:
                content_length_int = int(content_length)
                file_size_mb = content_length_int / 1024 / 1024
                logger.info(f"File size: {file_size_mb:.2f} MB")
                logger.info(f"Connect to source: {download_time:.2f}s")
            
            # Upload directly from stream in chunks (no intermediate storage)
            # This streams directly from Pexels to GCS without loading into memory
            upload_start = time.time()
            blob.upload_from_file(response.raw, rewind=False, size=content_length_int)
            upload_time = time.time() - upload_start
        
        total_time = time.time() - start_time
        
        logger.info(f"Upload to GCS: {upload_time:.2f}s")
        logger.info(f"Total time: {total_time:.2f}s")
        if file_size_mb > 0:
            speed_mbps = (file_size_mb / total_time) if total_time > 0 else 0
            logger.info(f"Speed: {speed_mbps:.2f} MB/s")
        logger.info(f"URL content streamed successfully to GCS: {blob_path}")
        
        # Generate signed URL with 7-day expiration
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=GCS_SIGNED_URL_EXPIRATION_DAYS * 24 * 60 * 60,  # Days to seconds
            method="GET"
        )
        
        logger.info(f"Generated signed URL (expires in {GCS_SIGNED_URL_EXPIRATION_DAYS} days)")
        return signed_url
        
    except Exception as e:
        logger.error(f"Failed to stream URL to GCS: {e}")
        raise


def delete_file_from_gcs(
    blob_path: str,
    bucket_name: str = GCS_BUCKET_NAME
) -> bool:
    """
    Delete a file from GCS.
    
    Args:
        blob_path: Full path to the blob (e.g., 'user_id/session_id/file.mp4')
        bucket_name: GCS bucket name
    
    Returns:
        bool: True if deleted successfully, False if file not found
    
    Raises:
        Exception: If deletion fails for reasons other than NotFound
    """
    try:
        bucket = get_or_create_bucket(bucket_name)
        blob = bucket.blob(blob_path)
        
        blob.delete()
        logger.info(f"File deleted successfully: {blob_path}")
        return True
        
    except NotFound:
        logger.warning(f"File not found for deletion: {blob_path}")
        return False
    except Exception as e:
        logger.error(f"Failed to delete file from GCS: {e}")
        raise


def get_signed_url(
    blob_path: str,
    expiration_days: int = None,
    bucket_name: str = GCS_BUCKET_NAME
) -> str:
    """
    Generate a signed URL for temporary access to a GCS file.
    
    Note: All upload functions now return signed URLs by default.
    This function is for generating new signed URLs for existing files.
    
    Args:
        blob_path: Full path to the blob
        expiration_days: How long the URL should be valid (default: from env or 7 days)
        bucket_name: GCS bucket name
    
    Returns:
        str: Signed URL with expiration
    
    Raises:
        Exception: If signing fails
    """
    try:
        if expiration_days is None:
            expiration_days = GCS_SIGNED_URL_EXPIRATION_DAYS
        
        bucket = get_or_create_bucket(bucket_name)
        blob = bucket.blob(blob_path)
        
        # Generate signed URL
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=expiration_days * 24 * 60 * 60,  # Days to seconds
            method="GET"
        )
        
        logger.info(f"Signed URL generated for: {blob_path} (expires in {expiration_days} days)")
        return signed_url
        
    except Exception as e:
        logger.error(f"Failed to generate signed URL: {e}")
        raise
