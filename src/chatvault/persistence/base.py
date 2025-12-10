"""
Base class for persistence backends.

Persistence backends handle storing and retrieving session data.
"""

from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from chatvault.session import Session


class PersistenceBackend(ABC):
    """
    Abstract base class for session persistence backends.
    
    Implementations should handle storing and retrieving Session objects.
    """
    
    @abstractmethod
    def save_session(self, session: "Session") -> None:
        """
        Save a session.
        
        Args:
            session: The session to save
        """
        pass
    
    @abstractmethod
    def get_session(self, session_id: str) -> Optional["Session"]:
        """
        Load a session by ID.
        
        Args:
            session_id: The session ID to load
            
        Returns:
            The Session if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_user_sessions(self, user_id: str) -> list["Session"]:
        """
        Get all sessions for a user.
        
        Args:
            user_id: The user ID to query
            
        Returns:
            List of sessions belonging to the user
        """
        pass
    
    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: The session ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    def list_sessions(self, limit: int = 100, offset: int = 0) -> list["Session"]:
        """
        List all sessions with pagination.
        
        Args:
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip
            
        Returns:
            List of sessions
        """
        raise NotImplementedError("list_sessions not implemented for this backend")
