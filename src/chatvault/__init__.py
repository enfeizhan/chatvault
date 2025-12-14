"""
ChatVault - AI Conversation & File Manager

Vault your conversations. Unlock your context.

Usage:
    from chatvault import ChatVault
    from chatvault.storage import LocalStorage
    from chatvault.persistence import MemoryBackend
    
    vault = ChatVault(
        storage=LocalStorage(base_path="./uploads"),
        persistence=MemoryBackend()
    )
    
    session = vault.create_session(user_id="user-123")
    session.add_message("user", "Hello!")

For FastAPI integration:
    from chatvault.api import create_router
    app.include_router(create_router(vault), prefix="/api")
"""

from chatvault.vault import ChatVault
from chatvault.session import Session, Message, FileAttachment

__version__ = "0.1.0"
__all__ = ["ChatVault", "Session", "Message", "FileAttachment"]

