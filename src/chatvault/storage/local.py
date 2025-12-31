"""
Local filesystem storage backend.

Stores files on the local filesystem. Great for development and testing.
"""

import os
from pathlib import Path
from typing import Optional
from chatvault.storage.base import StorageBackend


class LocalStorage(StorageBackend):
    """
    Local filesystem storage backend.
    
    Example:
        storage = LocalStorage(base_path="./uploads")
        storage.put("session-123/doc.pdf", file_bytes, "application/pdf")
        content = storage.get("session-123/doc.pdf")
    """
    
    def __init__(self, base_path: str = "./uploads"):
        """
        Initialize local storage.
        
        Args:
            base_path: Root directory for file storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_full_path(self, key: str) -> Path:
        """Get full filesystem path for a key."""
        return self.base_path / key
    
    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        """Store a file to the local filesystem."""
        full_path = self._get_full_path(key)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(data)
        
        # Store content type in a sidecar file
        meta_path = full_path.with_suffix(full_path.suffix + ".meta")
        meta_path.write_text(content_type)
    
    def get(self, key: str) -> Optional[bytes]:
        """Retrieve a file from the local filesystem."""
        full_path = self._get_full_path(key)
        if full_path.exists():
            return full_path.read_bytes()
        return None
    
    def delete(self, key: str) -> bool:
        """Delete a file from the local filesystem."""
        full_path = self._get_full_path(key)
        meta_path = full_path.with_suffix(full_path.suffix + ".meta")
        
        deleted = False
        if full_path.exists():
            full_path.unlink()
            deleted = True
        if meta_path.exists():
            meta_path.unlink()
        
        return deleted
    
    def exists(self, key: str) -> bool:
        """Check if a file exists."""
        return self._get_full_path(key).exists()
    
    def get_signed_url(
        self, 
        key: str, 
        expires_in: int = 3600,
        download_filename: Optional[str] = None,
    ) -> Optional[str]:
        """
        For local storage, return a file:// URL.
        
        Note: This is not secure for production use. Consider using
        a web server to serve files with proper access control.
        """
        full_path = self._get_full_path(key)
        if full_path.exists():
            return f"file://{full_path.absolute()}"
        return None
    
    def get_content_type(self, key: str) -> Optional[str]:
        """Get the content type of a stored file."""
        full_path = self._get_full_path(key)
        meta_path = full_path.with_suffix(full_path.suffix + ".meta")
        if meta_path.exists():
            return meta_path.read_text()
        return None
