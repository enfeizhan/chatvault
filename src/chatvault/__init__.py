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

For Chainlit UI (requires chatvault[ui]):
    from chatvault.ui import create_chainlit_app
    
    async def ai_handler(message, session):
        return await my_llm.chat(message)
    
    chainlit_app = create_chainlit_app(vault, ai_handler)
    app.mount("/chat", chainlit_app)
"""

from chatvault.vault import ChatVault
from chatvault.session import Session, Message, FileAttachment

__version__ = "0.1.0"
__all__ = ["ChatVault", "Session", "Message", "FileAttachment"]

