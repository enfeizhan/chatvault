"""Persistence backends for ChatVault."""

from chatvault.persistence.base import PersistenceBackend
from chatvault.persistence.memory import MemoryBackend

# Lazy imports for optional backends
def get_ots_backend():
    from chatvault.persistence.ots import OTSBackend
    return OTSBackend

__all__ = ["PersistenceBackend", "MemoryBackend", "get_ots_backend"]
