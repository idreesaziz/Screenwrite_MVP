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
from typing import Optional, BinaryIO
from google.cloud import storage
from google.cloud.exceptions import NotFound, Conflict
import requests

logger = logging.getLogger(__name__)

# Environment variables
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "screenwrite-media")
GCS_LOCATION = os.getenv("GCS_LOCATION", "us-central1")


def get_gcs_client() -> storage.Client:
    """
    Initialize and return a GCS client.
    
    Uses Application Default Credentials (ADC) which can be set via:
    - GOOGLE_APPLICATION_CREDENTIALS environment variable pointing to service account JSON
    - gcloud auth application-default login for local development
    
    Returns:
        storage.Client: Initialized GCS client
    """
    try:
        client = storage.Client()
        logger.info("GCS client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize GCS client: {e}")
        raise


def get_or_create_bucket(
    bucket_name: str = GCS_BUCKET_NAME,
    location: str = GCS_LOCATION
) -> storage.Bucket:
    """
    Get an existing bucket or create a new one with uniform bucket-level access.
    
    Args:
        bucket_name: Name of the GCS bucket
        location: GCS bucket location (e.g., 'us-central1')
    
    Returns:
        storage.Bucket: The GCS bucket object
    """
    client = get_gcs_client()
    
    try:
        bucket = client.get_bucket(bucket_name)
        logger.info(f"Bucket '{bucket_name}' already exists")
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
            return bucket
        except Conflict:
            # Race condition: bucket was created between check and create
            bucket = client.get_bucket(bucket_name)
            logger.info(f"Bucket '{bucket_name}' created by another process")
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
        
        # Return public URL
        public_url = blob.public_url
        return public_url
        
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
        # Download file from URL
        logger.info(f"Downloading file from URL: {url}")
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        # Extract filename from URL if not provided
        if not filename:
            filename = url.split('/')[-1].split('?')[0]
            if not filename:
                filename = f"downloaded_{uuid.uuid4()}"
        
        # Get content type from response headers
        content_type = response.headers.get('Content-Type')
        
        # Upload to GCS
        bucket = get_or_create_bucket(bucket_name)
        file_uuid = str(uuid.uuid4())
        blob_path = f"{user_id}/{session_id}/{file_uuid}_{filename}"
        
        blob = bucket.blob(blob_path)
        if content_type:
            blob.content_type = content_type
        
        # Upload from response stream
        blob.upload_from_file(response.raw, rewind=False)
        
        logger.info(f"URL content uploaded successfully to: {blob_path}")
        
        return blob.public_url
        
    except Exception as e:
        logger.error(f"Failed to upload URL to GCS: {e}")
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
    expiration_minutes: int = 60,
    bucket_name: str = GCS_BUCKET_NAME
) -> str:
    """
    Generate a signed URL for temporary access to a GCS file.
    
    Optional feature for providing time-limited access to files.
    Requires service account credentials with signing permissions.
    
    Args:
        blob_path: Full path to the blob
        expiration_minutes: How long the URL should be valid (default: 60 minutes)
        bucket_name: GCS bucket name
    
    Returns:
        str: Signed URL with expiration
    
    Raises:
        Exception: If signing fails
    """
    try:
        bucket = get_or_create_bucket(bucket_name)
        blob = bucket.blob(blob_path)
        
        # Generate signed URL
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=expiration_minutes * 60,  # Convert to seconds
            method="GET"
        )
        
        logger.info(f"Signed URL generated for: {blob_path}")
        return signed_url
        
    except Exception as e:
        logger.error(f"Failed to generate signed URL: {e}")
        raise
