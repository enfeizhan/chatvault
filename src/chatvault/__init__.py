"""
ChatVault - AI Conversation & File Manager

Vault your conversations. Unlock your context.

Usage:
    from chatvault import ChatVault, Conversation, Message, FileAttachment
    from chatvault.backends import MemoryMessages, LocalFiles
    
    vault = ChatVault(
        messages=MemoryMessages(),
        files=LocalFiles(base_path="./uploads"),
    )
    
    conversation = vault.create_conversation(user_id="user-123")
    conversation.add_message("user", "Hello!")

For FastAPI integration:
    from chatvault import create_router
    app.include_router(create_router(vault), prefix="/api")

Custom backends (implement the abstract base classes):
    from chatvault.backends import MessagesBackend, FilesBackend
"""

from chatvault.vault import ChatVault
from chatvault.conversation import Conversation, Message, FileAttachment
from chatvault.api import create_router

__all__ = [
    "ChatVault",
    "Conversation",
    "Message",
    "FileAttachment",
    "create_router",
]
