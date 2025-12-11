"""Storage backends for ChatVault."""

from chatvault.storage.base import StorageBackend
from chatvault.storage.local import LocalStorage

# Lazy imports for optional backends
def get_oss_storage():
    from chatvault.storage.oss import OSSStorage
    return OSSStorage

__all__ = ["StorageBackend", "LocalStorage", "get_oss_storage"]
