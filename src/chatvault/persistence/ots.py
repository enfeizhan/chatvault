"""
Alibaba Cloud OTS (Tablestore) persistence backend for ChatVault.

This module provides OTS-based session persistence for use with Alibaba Cloud.
"""

from typing import Optional
from datetime import datetime
import json
import logging

try:
    from tablestore import OTSClient, Row, Condition, RowExistenceExpectation, Direction
    HAS_OTS = True
except ImportError:
    HAS_OTS = False

from chatvault.persistence.base import PersistenceBackend
from chatvault.session import Session, Message, FileAttachment

logger = logging.getLogger(__name__)


class OTSBackend(PersistenceBackend):
    """
    Alibaba Cloud OTS (Tablestore) persistence backend.
    
    Stores sessions in an OTS table with the following schema:
    - Primary Key: session_id (STRING)
    - Columns: user_id, title, messages (JSON), files (JSON), 
               created_at, last_active, metadata (JSON)
    
    Example:
        from chatvault.persistence.ots import OTSBackend
        
        backend = OTSBackend(
            endpoint="https://instance.cn-shanghai.ots.aliyuncs.com",
            instance="instance-name",
            table="sessions",
            access_key_id="...",
            access_key_secret="..."
        )
    """
    
    def __init__(
        self,
        endpoint: str,
        instance: str,
        table: str = "sessions",
        access_key_id: Optional[str] = None,
        access_key_secret: Optional[str] = None,
        client: Optional["OTSClient"] = None,
    ):
        """
        Initialize OTS backend.
        
        Args:
            endpoint: OTS endpoint URL
            instance: OTS instance name
            table: Table name for sessions
            access_key_id: Alibaba Cloud access key ID
            access_key_secret: Alibaba Cloud access key secret
            client: Optional pre-configured OTSClient
        """
        if not HAS_OTS:
            raise ImportError("tablestore package is required. Install with: pip install tablestore")
        
        self.table = table
        
        if client:
            self._client = client
        else:
            self._client = OTSClient(
                endpoint,
                access_key_id,
                access_key_secret,
                instance
            )
    
    def save_session(self, session: Session) -> None:
        """Save a session to OTS."""
        primary_key = [('session_id', session.session_id)]
        
        attribute_columns = [
            ('user_id', session.user_id or ''),
            ('title', session.title),
            ('messages', json.dumps([m.to_dict() for m in session._messages], ensure_ascii=False)),
            ('files', json.dumps([f.to_dict() for f in session._files], ensure_ascii=False)),
            ('created_at', int(session.created_at.timestamp())),
            ('last_active', int(session.last_active.timestamp())),
            ('metadata', json.dumps(session.metadata, ensure_ascii=False)),
        ]
        
        row = Row(primary_key, attribute_columns)
        condition = Condition(RowExistenceExpectation.IGNORE)
        
        try:
            self._client.put_row(self.table, row, condition)
        except Exception as e:
            logger.error(f"Error saving session {session.session_id}: {e}")
            raise
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Load a session from OTS."""
        primary_key = [('session_id', session_id)]
        
        try:
            consumed, result, token = self._client.get_row(
                self.table,
                primary_key,
                max_version=1
            )
            
            if not result.row:
                return None
            
            return self._row_to_session(result.row)
            
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return None
    
    def get_user_sessions(self, user_id: str, limit: int = 50) -> list[Session]:
        """
        Get all sessions for a user.
        
        Note: This requires a secondary index on user_id for efficiency.
        Without an index, this does a full table scan which is slow.
        """
        # For now, use GetRange to scan (not efficient for large tables)
        # In production, create a secondary index on user_id
        sessions = []
        
        try:
            consumed, next_key, rows, token = self._client.get_range(
                self.table,
                Direction.FORWARD,
                [('session_id', '')],
                [('session_id', 'zzzzzzzzzzzzzzz')],  # Max string
                max_version=1,
                limit=1000  # Scan limit
            )
            
            for row in rows:
                attrs = {col[0]: col[1] for col in row.attribute_columns}
                if attrs.get('user_id') == user_id:
                    session = self._row_to_session(row)
                    if session:
                        sessions.append(session)
            
            # Sort by last_active descending
            sessions.sort(key=lambda s: s.last_active, reverse=True)
            return sessions[:limit]
            
        except Exception as e:
            logger.error(f"Error getting user sessions for {user_id}: {e}")
            return []
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session from OTS."""
        primary_key = [('session_id', session_id)]
        condition = Condition(RowExistenceExpectation.IGNORE)
        
        try:
            self._client.delete_row(self.table, primary_key, condition)
            return True
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False
    
    def _row_to_session(self, row) -> Optional[Session]:
        """Convert an OTS row to a Session object."""
        try:
            session_id = row.primary_key[0][1]
            attrs = {col[0]: col[1] for col in row.attribute_columns}
            
            messages = []
            if attrs.get('messages'):
                messages = [Message.from_dict(m) for m in json.loads(attrs['messages'])]
            
            files = []
            if attrs.get('files'):
                files = [FileAttachment.from_dict(f) for f in json.loads(attrs['files'])]
            
            metadata = {}
            if attrs.get('metadata'):
                metadata = json.loads(attrs['metadata'])
            
            return Session(
                session_id=session_id,
                user_id=attrs.get('user_id') or None,
                title=attrs.get('title', ''),
                created_at=datetime.fromtimestamp(attrs.get('created_at', 0)),
                messages=messages,
                files=files,
                metadata=metadata,
            )
        except Exception as e:
            logger.error(f"Error parsing session row: {e}")
            return None
