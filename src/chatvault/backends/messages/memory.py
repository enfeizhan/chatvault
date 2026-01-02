"""
In-memory messages backend.

Stores conversations in memory. Great for development and testing.
Note: Data is lost when the process exits.
"""

from typing import Optional
from chatvault.backends.messages.base import MessagesBackend
from chatvault.conversation import Conversation


class MemoryMessages(MessagesBackend):
    """
    In-memory messages backend.
    
    Stores all conversations in a Python dict. Data is not persisted across restarts.
    
    Example:
        messages = MemoryMessages()
        vault = ChatVault(messages=messages, files=...)
    """
    
    def __init__(self):
        """Initialize empty conversation store."""
        self._conversations: dict[str, dict] = {}
    
    def save(self, conversation: Conversation) -> None:
        """Save a conversation to memory."""
        self._conversations[conversation.conversation_id] = conversation.to_dict()
    
    def get(self, conversation_id: str) -> Optional[Conversation]:
        """Load a conversation from memory."""
        data = self._conversations.get(conversation_id)
        if data:
            return Conversation.from_dict(data)
        return None
    
    def get_by_user(self, user_id: str) -> list[Conversation]:
        """Get all conversations for a user."""
        conversations = []
        for data in self._conversations.values():
            if data.get("user_id") == user_id:
                conversations.append(Conversation.from_dict(data))
        
        # Sort by last_active descending
        conversations.sort(key=lambda c: c.last_active, reverse=True)
        return conversations
    
    def delete(self, conversation_id: str) -> bool:
        """Delete a conversation from memory."""
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            return True
        return False
    
    def list(self, limit: int = 100, offset: int = 0) -> list[Conversation]:
        """List all conversations with pagination."""
        all_conversations = [Conversation.from_dict(data) for data in self._conversations.values()]
        all_conversations.sort(key=lambda c: c.last_active, reverse=True)
        return all_conversations[offset:offset + limit]
    
    def clear(self) -> None:
        """Clear all conversations. Useful for testing."""
        self._conversations.clear()
