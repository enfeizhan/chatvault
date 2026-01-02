"""
Conversation model for ChatVault.

A conversation represents a single chat thread with message history and file attachments.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any
from uuid import uuid4


@dataclass
class Message:
    """A single message in a conversation."""
    
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )


@dataclass
class FileAttachment:
    """A file attached to a conversation."""
    
    filename: str
    content_type: str
    size: int
    storage_key: str  # Key in the storage backend
    uploaded_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "content_type": self.content_type,
            "size": self.size,
            "storage_key": self.storage_key,
            "uploaded_at": self.uploaded_at.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "FileAttachment":
        return cls(
            filename=data["filename"],
            content_type=data["content_type"],
            size=data["size"],
            storage_key=data["storage_key"],
            uploaded_at=datetime.fromisoformat(data["uploaded_at"]),
            metadata=data.get("metadata", {}),
        )


class Conversation:
    """
    A conversation with messages and file attachments.
    
    This class is typically created via ChatVault.create_conversation() or
    ChatVault.get_conversation(), not instantiated directly.
    """
    
    def __init__(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
        title: Optional[str] = None,
        created_at: Optional[datetime] = None,
        messages: Optional[list[Message]] = None,
        files: Optional[list[FileAttachment]] = None,
        metadata: Optional[dict[str, Any]] = None,
        # Internal references (set by ChatVault)
        _vault: Optional[Any] = None,
    ):
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.title = title or ""
        self.created_at = created_at or datetime.now()
        self.last_active = self.created_at
        self._messages = messages or []
        self._files = files or []
        self.metadata = metadata or {}
        self._vault = _vault
    
    @classmethod
    def new(cls, user_id: Optional[str] = None, **kwargs) -> "Conversation":
        """Create a new conversation with a generated ID."""
        return cls(
            conversation_id=str(uuid4()),
            user_id=user_id,
            **kwargs,
        )
    
    def add_message(self, role: str, content: str, **metadata) -> Message:
        """Add a message to the conversation."""
        message = Message(role=role, content=content, metadata=metadata)
        self._messages.append(message)
        self.last_active = datetime.now()
        self._auto_title()
        self._save()
        return message
    
    def get_messages(self) -> list[Message]:
        """Get all messages in the conversation."""
        return self._messages.copy()
    
    def get_history(self) -> list[dict]:
        """Get message history in LLM-compatible format."""
        return [{"role": m.role, "content": m.content} for m in self._messages]
    
    def attach_file(
        self,
        filename: str,
        content: bytes,
        content_type: str = "application/octet-stream",
        **metadata,
    ) -> FileAttachment:
        """Attach a file to the conversation."""
        if not self._vault:
            raise RuntimeError("Conversation not connected to a vault")
        
        # Generate storage key: user_id/conversation_id/filename (or conversation_id/filename if no user)
        if self.user_id:
            storage_key = f"{self.user_id}/{self.conversation_id}/{filename}"
        else:
            storage_key = f"{self.conversation_id}/{filename}"
        
        # Upload to files backend
        self._vault._files.upload(storage_key, content, content_type)
        
        # Create attachment record
        attachment = FileAttachment(
            filename=filename,
            content_type=content_type,
            size=len(content),
            storage_key=storage_key,
            metadata=metadata,
        )
        self._files.append(attachment)
        self._save()
        return attachment
    
    def get_files(self) -> list[FileAttachment]:
        """Get all file attachments."""
        return self._files.copy()
    
    def get_file_url(self, filename: str, expires_in: int = 3600) -> Optional[str]:
        """Get a signed URL for downloading a file."""
        if not self._vault:
            raise RuntimeError("Conversation not connected to a vault")
        
        for f in self._files:
            if f.filename == filename:
                # Pass download_filename to force download with original filename
                return self._vault._files.get_signed_url(
                    f.storage_key, 
                    expires_in, 
                    download_filename=f.filename
                )
        return None
    
    def get_file_content(self, filename: str) -> Optional[bytes]:
        """Download file content directly."""
        if not self._vault:
            raise RuntimeError("Conversation not connected to a vault")
        
        for f in self._files:
            if f.filename == filename:
                return self._vault._files.download(f.storage_key)
        return None
    
    def rename(self, title: str) -> None:
        """Rename the conversation."""
        self.title = title
        self._save()
    
    def _auto_title(self) -> None:
        """Auto-generate title from first user message if not set."""
        if not self.title and self._messages:
            for m in self._messages:
                if m.role == "user":
                    # Use first 50 chars of first user message
                    self.title = m.content[:50] + ("..." if len(m.content) > 50 else "")
                    break
    
    def _save(self) -> None:
        """Persist conversation to storage."""
        if self._vault:
            self._vault._messages.save(self)
    
    def to_dict(self) -> dict:
        """Serialize conversation to dictionary."""
        return {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "title": self.title,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "messages": [m.to_dict() for m in self._messages],
            "files": [f.to_dict() for f in self._files],
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict, vault: Optional[Any] = None) -> "Conversation":
        """Deserialize conversation from dictionary."""
        return cls(
            conversation_id=data["conversation_id"],
            user_id=data.get("user_id"),
            title=data.get("title", ""),
            created_at=datetime.fromisoformat(data["created_at"]),
            messages=[Message.from_dict(m) for m in data.get("messages", [])],
            files=[FileAttachment.from_dict(f) for f in data.get("files", [])],
            metadata=data.get("metadata", {}),
            _vault=vault,
        )
