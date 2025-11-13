"""Abstract base class for cloud storage providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import BinaryIO, Optional, List, Dict, Any
from datetime import datetime


@dataclass
class StorageFile:
    """Metadata for a stored file."""
    path: str
    name: str
    size: int
    content_type: Optional[str]
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class UploadResult:
    """Result of a file upload operation."""
    path: str
    url: str
    signed_url: Optional[str]
    size: int
    content_type: Optional[str]
    metadata: Optional[Dict[str, Any]] = None
    sanitized_filename: Optional[str] = None  # The actual filename used in storage


class StorageProvider(ABC):
    """
    Abstract interface for cloud storage providers.
    
    Provides consistent interface for:
    - File upload/download operations
    - URL generation (signed/public)
    - File management (delete, list, exists)
    - Bucket/container management
    """
    
    @abstractmethod
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
        """
        Upload a file from binary stream with user/session isolation.
        
        Path structure: {user_id}/{session_id}/{uuid}_{filename}
        
        Args:
            file_data: File-like object opened in binary mode
            user_id: User ID for isolation
            session_id: Session ID for isolation
            filename: Original filename
            content_type: MIME type (e.g., 'video/mp4', 'image/png')
            metadata: Additional metadata to store with file
            **kwargs: Provider-specific options
            
        Returns:
            UploadResult with path, URLs, and metadata
        """
        pass
    
    @abstractmethod
    async def upload_from_url(
        self,
        url: str,
        user_id: str,
        session_id: str,
        filename: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> UploadResult:
        """
        Download file from URL and upload to storage.
        
        Useful for stock media APIs, generated content, etc.
        Should stream directly without loading into memory.
        
        Args:
            url: Source URL to download from
            user_id: User ID for isolation
            session_id: Session ID for isolation
            filename: Optional filename (extracted from URL if not provided)
            metadata: Additional metadata
            **kwargs: Provider-specific options
            
        Returns:
            UploadResult with path, URLs, and metadata
        """
        pass
    
    @abstractmethod
    async def download_file(
        self,
        path: str,
        **kwargs
    ) -> bytes:
        """
        Download file content as bytes.
        
        Args:
            path: Full path to file in storage
            **kwargs: Provider-specific options
            
        Returns:
            File content as bytes
        """
        pass
    
    @abstractmethod
    async def delete_file(
        self,
        path: str,
        **kwargs
    ) -> bool:
        """
        Delete a file from storage.
        
        Args:
            path: Full path to file
            **kwargs: Provider-specific options
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def file_exists(
        self,
        path: str,
        **kwargs
    ) -> bool:
        """
        Check if file exists in storage.
        
        Args:
            path: Full path to file
            **kwargs: Provider-specific options
            
        Returns:
            True if file exists
        """
        pass
    
    @abstractmethod
    async def list_files(
        self,
        prefix: str,
        limit: Optional[int] = None,
        **kwargs
    ) -> List[StorageFile]:
        """
        List files with given prefix.
        
        Args:
            prefix: Path prefix to filter by (e.g., 'user_id/session_id/')
            limit: Maximum number of files to return
            **kwargs: Provider-specific options
            
        Returns:
            List of StorageFile objects
        """
        pass
    
    @abstractmethod
    async def generate_signed_url(
        self,
        path: str,
        expiration_seconds: int = 604800,  # 7 days default
        **kwargs
    ) -> str:
        """
        Generate a signed URL for temporary access.
        
        Args:
            path: Full path to file
            expiration_seconds: How long URL is valid (default: 7 days)
            **kwargs: Provider-specific options
            
        Returns:
            Signed URL string
        """
        pass
    
    @abstractmethod
    async def get_public_url(
        self,
        path: str,
        **kwargs
    ) -> str:
        """
        Get public URL for a file (if public access enabled).
        
        Args:
            path: Full path to file
            **kwargs: Provider-specific options
            
        Returns:
            Public URL string
        """
        pass
