"""
ChatVault - Main vault class.

The ChatVault is the primary interface for managing sessions and files.
"""

from typing import Optional
from chatvault.session import Session
from chatvault.storage.base import StorageBackend
from chatvault.persistence.base import PersistenceBackend


class ChatVault:
    """
    Main ChatVault class for managing AI conversation sessions.
    
    Example:
        vault = ChatVault(
            storage=LocalStorage(base_path="./uploads"),
            persistence=MemoryBackend()
        )
        
        session = vault.create_session(user_id="user-123")
        session.add_message("user", "Hello!")
    """
    
    def __init__(
        self,
        storage: StorageBackend,
        persistence: PersistenceBackend,
    ):
        """
        Initialize ChatVault.
        
        Args:
            storage: Backend for storing file attachments
            persistence: Backend for storing session data
        """
        self._storage = storage
        self._persistence = persistence
    
    def create_session(self, user_id: Optional[str] = None, **metadata) -> Session:
        """
        Create a new conversation session.
        
        Args:
            user_id: Optional user ID to associate with the session
            **metadata: Additional metadata to store with the session
            
        Returns:
            A new Session instance
        """
        session = Session.new(user_id=user_id, metadata=metadata, _vault=self)
        self._persistence.save_session(session)
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Load an existing session by ID.
        
        Args:
            session_id: The session ID to load
            
        Returns:
            The Session if found, None otherwise
        """
        session = self._persistence.get_session(session_id)
        if session:
            session._vault = self
        return session
    
    def get_user_sessions(self, user_id: str) -> list[Session]:
        """
        Get all sessions for a user.
        
        Args:
            user_id: The user ID to query
            
        Returns:
            List of sessions belonging to the user
        """
        sessions = self._persistence.get_user_sessions(user_id)
        for session in sessions:
            session._vault = self
        return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and its associated files.
        
        Args:
            session_id: The session ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        # Delete files from storage
        for f in session.get_files():
            self._storage.delete(f.storage_key)
        
        # Delete session from persistence
        return self._persistence.delete_session(session_id)
    
    def archive_session(self, session_id: str) -> bool:
        """
        Archive a session (mark as inactive).
        
        Args:
            session_id: The session ID to archive
            
        Returns:
            True if archived, False if not found
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.metadata["archived"] = True
        self._persistence.save_session(session)
        return True
