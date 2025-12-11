"""
Alibaba Cloud OSS storage backend for ChatVault.

This module provides OSS-based file storage for use with Alibaba Cloud.
"""

from typing import Optional
import logging

try:
    import oss2
    HAS_OSS = True
except ImportError:
    HAS_OSS = False

from chatvault.storage.base import StorageBackend

logger = logging.getLogger(__name__)


class OSSStorage(StorageBackend):
    """
    Alibaba Cloud OSS storage backend.
    
    Stores files in an OSS bucket with configurable key prefixes.
    
    Example:
        from chatvault.storage.oss import OSSStorage
        
        storage = OSSStorage(
            endpoint="https://oss-cn-shanghai.aliyuncs.com",
            bucket="my-bucket",
            access_key_id="...",
            access_key_secret="...",
            prefix="chatvault/"  # Optional key prefix
        )
    """
    
    def __init__(
        self,
        endpoint: str,
        bucket: str,
        access_key_id: str,
        access_key_secret: str,
        prefix: str = "",
    ):
        """
        Initialize OSS storage.
        
        Args:
            endpoint: OSS endpoint URL
            bucket: OSS bucket name
            access_key_id: Alibaba Cloud access key ID
            access_key_secret: Alibaba Cloud access key secret
            prefix: Optional key prefix for all stored files
        """
        if not HAS_OSS:
            raise ImportError("oss2 package is required. Install with: pip install oss2")
        
        self.prefix = prefix
        
        auth = oss2.Auth(access_key_id, access_key_secret)
        self._bucket = oss2.Bucket(auth, endpoint, bucket)
    
    def _get_key(self, key: str) -> str:
        """Get full key with prefix."""
        return f"{self.prefix}{key}"
    
    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        """Store a file to OSS."""
        full_key = self._get_key(key)
        headers = {'Content-Type': content_type}
        
        try:
            self._bucket.put_object(full_key, data, headers=headers)
            logger.debug(f"Uploaded to OSS: {full_key}")
        except Exception as e:
            logger.error(f"Error uploading to OSS {full_key}: {e}")
            raise
    
    def get(self, key: str) -> Optional[bytes]:
        """Retrieve a file from OSS."""
        full_key = self._get_key(key)
        
        try:
            result = self._bucket.get_object(full_key)
            return result.read()
        except oss2.exceptions.NoSuchKey:
            return None
        except Exception as e:
            logger.error(f"Error getting from OSS {full_key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a file from OSS."""
        full_key = self._get_key(key)
        
        try:
            self._bucket.delete_object(full_key)
            return True
        except Exception as e:
            logger.error(f"Error deleting from OSS {full_key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if a file exists in OSS."""
        full_key = self._get_key(key)
        return self._bucket.object_exists(full_key)
    
    def get_signed_url(self, key: str, expires_in: int = 3600) -> Optional[str]:
        """
        Generate a signed URL for downloading a file.
        
        Args:
            key: Storage key
            expires_in: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Signed URL string
        """
        full_key = self._get_key(key)
        
        try:
            url = self._bucket.sign_url('GET', full_key, expires_in)
            return url
        except Exception as e:
            logger.error(f"Error generating signed URL for {full_key}: {e}")
            return None
