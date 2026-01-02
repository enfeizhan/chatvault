"""
Base class for messages backends.

Messages backends handle storing and retrieving conversation data.
"""

from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from chatvault.conversation import Conversation


class MessagesBackend(ABC):
    """
    Abstract base class for conversation persistence backends.
    
    Implementations should handle storing and retrieving Conversation objects.
    """
    
    @abstractmethod
    def save(self, conversation: "Conversation") -> None:
        """
        Save a conversation.
        
        Args:
            conversation: The conversation to save
        """
        pass
    
    @abstractmethod
    def get(self, conversation_id: str) -> Optional["Conversation"]:
        """
        Load a conversation by ID.
        
        Args:
            conversation_id: The conversation ID to load
            
        Returns:
            The Conversation if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_by_user(self, user_id: str) -> list["Conversation"]:
        """
        Get all conversations for a user.
        
        Args:
            user_id: The user ID to query
            
        Returns:
            List of conversations belonging to the user
        """
        pass
    
    @abstractmethod
    def delete(self, conversation_id: str) -> bool:
        """
        Delete a conversation.
        
        Args:
            conversation_id: The conversation ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    def list(self, limit: int = 100, offset: int = 0) -> list["Conversation"]:
        """
        List all conversations with pagination.
        
        Args:
            limit: Maximum number of conversations to return
            offset: Number of conversations to skip
            
        Returns:
            List of conversations
        """
        raise NotImplementedError("list not implemented for this backend")
