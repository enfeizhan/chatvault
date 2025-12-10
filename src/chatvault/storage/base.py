"""
Base class for storage backends.

Storage backends handle file uploads, downloads, and signed URL generation.
"""

from abc import ABC, abstractmethod
from typing import Optional


class StorageBackend(ABC):
    """
    Abstract base class for file storage backends.
    
    Implementations should handle storing and retrieving binary file data.
    """
    
    @abstractmethod
    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        """
        Store a file.
        
        Args:
            key: Unique storage key (e.g., "session-id/filename.pdf")
            data: File contents as bytes
            content_type: MIME type of the file
        """
        pass
    
    @abstractmethod
    def get(self, key: str) -> Optional[bytes]:
        """
        Retrieve a file.
        
        Args:
            key: Storage key
            
        Returns:
            File contents as bytes, or None if not found
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Delete a file.
        
        Args:
            key: Storage key
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        Check if a file exists.
        
        Args:
            key: Storage key
            
        Returns:
            True if exists, False otherwise
        """
        pass
    
    def get_signed_url(self, key: str, expires_in: int = 3600) -> Optional[str]:
        """
        Generate a signed URL for downloading a file.
        
        Args:
            key: Storage key
            expires_in: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Signed URL string, or None if not supported
            
        Note:
            This is optional - local storage may return file:// URLs,
            while cloud storage returns signed HTTPS URLs.
        """
        return None
