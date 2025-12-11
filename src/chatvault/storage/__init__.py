"""Storage backends for ChatVault."""

from chatvault.storage.base import StorageBackend
from chatvault.storage.local import LocalStorage

__all__ = ["StorageBackend", "LocalStorage"]
