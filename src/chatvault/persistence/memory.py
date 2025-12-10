"""
In-memory persistence backend.

Stores sessions in memory. Great for development and testing.
Note: Data is lost when the process exits.
"""

from typing import Optional
from chatvault.persistence.base import PersistenceBackend
from chatvault.session import Session


class MemoryBackend(PersistenceBackend):
    """
    In-memory persistence backend.
    
    Stores all sessions in a Python dict. Data is not persisted across restarts.
    
    Example:
        persistence = MemoryBackend()
        vault = ChatVault(storage=..., persistence=persistence)
    """
    
    def __init__(self):
        """Initialize empty session store."""
        self._sessions: dict[str, dict] = {}
    
    def save_session(self, session: Session) -> None:
        """Save a session to memory."""
        self._sessions[session.session_id] = session.to_dict()
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Load a session from memory."""
        data = self._sessions.get(session_id)
        if data:
            return Session.from_dict(data)
        return None
    
    def get_user_sessions(self, user_id: str) -> list[Session]:
        """Get all sessions for a user."""
        sessions = []
        for data in self._sessions.values():
            if data.get("user_id") == user_id:
                sessions.append(Session.from_dict(data))
        
        # Sort by last_active descending
        sessions.sort(key=lambda s: s.last_active, reverse=True)
        return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session from memory."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    def list_sessions(self, limit: int = 100, offset: int = 0) -> list[Session]:
        """List all sessions with pagination."""
        all_sessions = [Session.from_dict(data) for data in self._sessions.values()]
        all_sessions.sort(key=lambda s: s.last_active, reverse=True)
        return all_sessions[offset:offset + limit]
    
    def clear(self) -> None:
        """Clear all sessions. Useful for testing."""
        self._sessions.clear()
