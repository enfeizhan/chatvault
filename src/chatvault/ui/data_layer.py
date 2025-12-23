"""
ChatVault Data Layer - Chainlit data persistence backed by ChatVault.

This module implements Chainlit's BaseDataLayer interface using ChatVault
for storage, enabling conversation history sidebar and thread persistence.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, List, Any
from uuid import uuid4

logger = logging.getLogger(__name__)


class ChatVaultDataLayer:
    """
    Chainlit data layer backed by ChatVault.
    
    Maps Chainlit concepts to ChatVault:
    - Thread → Session
    - Step → Message
    - Element → FileAttachment
    """
    
    def __init__(self, vault):
        """
        Initialize with a ChatVault instance.
        
        Args:
            vault: ChatVault instance for persistence
        """
        self.vault = vault
        self._users: Dict[str, dict] = {}  # In-memory user cache
        self._elements: Dict[str, dict] = {}  # In-memory element cache
        self._feedback: Dict[str, dict] = {}  # In-memory feedback cache
    
    # -------------------------------------------------------------------------
    # User Methods
    # -------------------------------------------------------------------------
    
    async def get_user(self, identifier: str):
        """Get a user by identifier."""
        if identifier in self._users:
            return self._users[identifier]
        return None
    
    async def create_user(self, user):
        """Create or update a user."""
        user_dict = {
            "id": user.identifier,
            "identifier": user.identifier,
            "metadata": getattr(user, "metadata", {}),
            "createdAt": datetime.now().isoformat(),
        }
        self._users[user.identifier] = user_dict
        logger.info(f"Created user: {user.identifier}")
        return user_dict
    
    # -------------------------------------------------------------------------
    # Feedback Methods
    # -------------------------------------------------------------------------
    
    async def delete_feedback(self, feedback_id: str) -> bool:
        """Delete feedback by ID."""
        if feedback_id in self._feedback:
            del self._feedback[feedback_id]
            return True
        return False
    
    async def upsert_feedback(self, feedback) -> str:
        """Create or update feedback."""
        feedback_id = getattr(feedback, "id", None) or str(uuid4())
        self._feedback[feedback_id] = {
            "id": feedback_id,
            "forId": getattr(feedback, "forId", None),
            "value": getattr(feedback, "value", None),
            "comment": getattr(feedback, "comment", None),
        }
        return feedback_id
    
    # -------------------------------------------------------------------------
    # Element Methods  
    # -------------------------------------------------------------------------
    
    async def create_element(self, element):
        """Create an element (file/image/etc)."""
        element_dict = {
            "id": element.id,
            "threadId": element.thread_id,
            "type": element.type,
            "name": element.name,
            "path": getattr(element, "path", None),
            "url": getattr(element, "url", None),
            "display": getattr(element, "display", "inline"),
            "mime": getattr(element, "mime", None),
        }
        self._elements[element.id] = element_dict
        logger.debug(f"Created element: {element.id}")
    
    async def get_element(self, thread_id: str, element_id: str):
        """Get an element by ID."""
        element = self._elements.get(element_id)
        if element and element.get("threadId") == thread_id:
            return element
        return None
    
    async def delete_element(self, element_id: str, thread_id: Optional[str] = None):
        """Delete an element."""
        if element_id in self._elements:
            del self._elements[element_id]
    
    # -------------------------------------------------------------------------
    # Step Methods (Steps = Messages in ChatVault)
    # -------------------------------------------------------------------------
    
    async def create_step(self, step_dict: dict):
        """Create a step (message) in a thread (session)."""
        thread_id = step_dict.get("threadId")
        if not thread_id:
            logger.warning("create_step called without threadId")
            return
        
        session = self.vault.get_session(thread_id)
        if not session:
            logger.warning(f"Session not found for thread: {thread_id}")
            return
        
        # Map step to message
        step_type = step_dict.get("type", "")
        if step_type == "user_message":
            role = "user"
        elif step_type in ("assistant_message", "run"):
            role = "assistant"
        else:
            role = "system"
        
        content = step_dict.get("output") or step_dict.get("input") or ""
        if content:
            session.add_message(role, content)
            logger.debug(f"Added {role} message to session {thread_id}")
    
    async def update_step(self, step_dict: dict):
        """Update a step - currently no-op as messages are immutable."""
        # ChatVault messages are immutable, so we skip updates
        pass
    
    async def delete_step(self, step_id: str):
        """Delete a step - currently no-op."""
        # ChatVault doesn't support message deletion
        pass
    
    # -------------------------------------------------------------------------
    # Thread Methods (Threads = Sessions in ChatVault)
    # -------------------------------------------------------------------------
    
    async def get_thread_author(self, thread_id: str) -> str:
        """Get the author (user_id) of a thread."""
        session = self.vault.get_session(thread_id)
        if session:
            return session.user_id or ""
        return ""
    
    async def delete_thread(self, thread_id: str):
        """Delete a thread (session)."""
        self.vault.delete_session(thread_id)
        logger.info(f"Deleted thread: {thread_id}")
    
    async def list_threads(self, pagination, filters):
        """List threads (sessions) for a user with pagination."""
        user_id = getattr(filters, "userId", None) if filters else None
        
        if not user_id:
            # No user filter, return empty
            return {"data": [], "pageInfo": {"hasNextPage": False}}
        
        # Get user sessions
        sessions = self.vault.get_user_sessions(user_id)
        
        # Sort by last_active descending
        sessions.sort(key=lambda s: s.last_active, reverse=True)
        
        # Apply pagination
        first = getattr(pagination, "first", 10) if pagination else 10
        cursor = getattr(pagination, "cursor", None) if pagination else None
        
        # Simple cursor-based pagination (cursor = session_id)
        start_idx = 0
        if cursor:
            for i, s in enumerate(sessions):
                if s.session_id == cursor:
                    start_idx = i + 1
                    break
        
        page = sessions[start_idx:start_idx + first]
        has_next = len(sessions) > start_idx + first
        
        # Convert to ThreadDict format
        threads = []
        for session in page:
            thread = self._session_to_thread(session)
            threads.append(thread)
        
        return {
            "data": threads,
            "pageInfo": {
                "hasNextPage": has_next,
                "endCursor": page[-1].session_id if page else None,
            }
        }
    
    async def get_thread(self, thread_id: str):
        """Get a thread (session) by ID."""
        session = self.vault.get_session(thread_id)
        if not session:
            return None
        
        return self._session_to_thread(session, include_steps=True)
    
    async def update_thread(
        self,
        thread_id: str,
        name: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
        tags: Optional[List[str]] = None,
    ):
        """Update a thread (session)."""
        session = self.vault.get_session(thread_id)
        if not session:
            return
        
        if name is not None:
            session.rename(name)
        
        if metadata is not None:
            session.metadata.update(metadata)
        
        if tags is not None:
            session.metadata["tags"] = tags
        
        # Trigger save
        session._save()
        logger.debug(f"Updated thread: {thread_id}")
    
    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------
    
    def _session_to_thread(self, session, include_steps: bool = False) -> dict:
        """Convert a ChatVault Session to a Chainlit ThreadDict."""
        thread = {
            "id": session.session_id,
            "createdAt": session.created_at.isoformat(),
            "name": session.title or None,
            "userId": session.user_id,
            "userIdentifier": session.user_id,
            "tags": session.metadata.get("tags", []),
            "metadata": session.metadata,
            "steps": [],
            "elements": [],
        }
        
        if include_steps:
            # Convert messages to steps
            for i, msg in enumerate(session.get_messages()):
                step_type = "user_message" if msg.role == "user" else "assistant_message"
                step = {
                    "id": f"{session.session_id}-{i}",
                    "threadId": session.session_id,
                    "type": step_type,
                    "name": msg.role,
                    "input": msg.content if msg.role == "user" else "",
                    "output": msg.content if msg.role != "user" else "",
                    "createdAt": msg.timestamp.isoformat(),
                    "streaming": False,
                    "metadata": msg.metadata,
                }
                thread["steps"].append(step)
            
            # Convert files to elements
            for file in session.get_files():
                element = {
                    "id": file.storage_key,
                    "threadId": session.session_id,
                    "type": "file",
                    "name": file.filename,
                    "mime": file.content_type,
                    "display": "side",
                }
                thread["elements"].append(element)
        
        return thread
    
    async def build_debug_url(self) -> str:
        """Build a debug URL - not applicable for ChatVault."""
        return ""
    
    async def close(self) -> None:
        """Close the data layer connection."""
        # No cleanup needed for ChatVault
        pass
