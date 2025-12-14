"""
ChatVault FastAPI Router.

Provides pre-built endpoints for conversation management.
"""

from typing import Optional, Callable, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Response
from pydantic import BaseModel
from datetime import datetime


# Request/Response Models
class ConversationCreate(BaseModel):
    """Request to create a new conversation."""
    title: Optional[str] = None
    metadata: Optional[dict] = None


class ConversationUpdate(BaseModel):
    """Request to update a conversation (e.g., rename)."""
    title: Optional[str] = None
    metadata: Optional[dict] = None


class MessageCreate(BaseModel):
    """Request to add a message."""
    role: str
    content: str
    metadata: Optional[dict] = None


class ConversationSummary(BaseModel):
    """Summary of a conversation for list views."""
    session_id: str
    title: str
    created_at: datetime
    last_active: datetime
    message_count: int
    file_count: int


class ConversationDetail(BaseModel):
    """Full conversation details."""
    session_id: str
    user_id: Optional[str]
    title: str
    created_at: datetime
    last_active: datetime
    messages: list[dict]
    files: list[dict]
    metadata: dict


class MessageResponse(BaseModel):
    """Response after adding a message."""
    role: str
    content: str
    timestamp: datetime


def create_router(
    vault: Any,
    get_user_id: Optional[Callable] = None,
    prefix: str = "/conversations",
) -> APIRouter:
    """
    Create a FastAPI router for ChatVault conversation management.
    
    Args:
        vault: ChatVault instance
        get_user_id: Optional dependency function that returns user_id.
                     If not provided, user_id must be passed in requests.
        prefix: URL prefix for all routes (default: "/conversations")
    
    Returns:
        FastAPI APIRouter with all conversation endpoints
    
    Example:
        vault = ChatVault(storage=..., persistence=...)
        
        # Simple usage
        app.include_router(create_router(vault), prefix="/api")
        
        # With authentication
        def get_current_user():
            # Your auth logic
            return user_id
        
        app.include_router(
            create_router(vault, get_user_id=get_current_user),
            prefix="/api"
        )
    """
    router = APIRouter(prefix=prefix, tags=["conversations"])
    
    # Default user_id dependency (returns None if not provided)
    async def default_get_user_id():
        return None
    
    user_id_dep = get_user_id or default_get_user_id
    
    @router.get("", response_model=list[ConversationSummary])
    async def list_conversations(user_id: str = Depends(user_id_dep)):
        """List all conversations for the current user."""
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        sessions = vault.get_user_sessions(user_id)
        return [
            ConversationSummary(
                session_id=s.session_id,
                title=s.title or "New Conversation",
                created_at=s.created_at,
                last_active=s.last_active,
                message_count=len(s._messages),
                file_count=len(s._files),
            )
            for s in sessions
        ]
    
    @router.post("", response_model=ConversationDetail)
    async def create_conversation(
        data: Optional[ConversationCreate] = None,
        user_id: str = Depends(user_id_dep),
    ):
        """Create a new conversation."""
        metadata = (data.metadata if data and data.metadata else {}) or {}
        session = vault.create_session(user_id=user_id, **metadata)
        
        if data and data.title:
            session.rename(data.title)
        
        return ConversationDetail(
            session_id=session.session_id,
            user_id=session.user_id,
            title=session.title,
            created_at=session.created_at,
            last_active=session.last_active,
            messages=[],
            files=[],
            metadata=session.metadata,
        )
    
    @router.get("/{session_id}", response_model=ConversationDetail)
    async def get_conversation(
        session_id: str,
        user_id: str = Depends(user_id_dep),
    ):
        """Get a conversation by ID."""
        session = vault.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Check ownership if user_id is available
        if user_id and session.user_id and session.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return ConversationDetail(
            session_id=session.session_id,
            user_id=session.user_id,
            title=session.title,
            created_at=session.created_at,
            last_active=session.last_active,
            messages=[m.to_dict() for m in session._messages],
            files=[f.to_dict() for f in session._files],
            metadata=session.metadata,
        )
    
    @router.patch("/{session_id}", response_model=ConversationDetail)
    async def update_conversation(
        session_id: str,
        data: ConversationUpdate,
        user_id: str = Depends(user_id_dep),
    ):
        """Update a conversation (rename, update metadata)."""
        session = vault.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Check ownership
        if user_id and session.user_id and session.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if data.title is not None:
            session.rename(data.title)
        
        if data.metadata is not None:
            session.metadata.update(data.metadata)
            session._save()
        
        return ConversationDetail(
            session_id=session.session_id,
            user_id=session.user_id,
            title=session.title,
            created_at=session.created_at,
            last_active=session.last_active,
            messages=[m.to_dict() for m in session._messages],
            files=[f.to_dict() for f in session._files],
            metadata=session.metadata,
        )
    
    @router.delete("/{session_id}")
    async def delete_conversation(
        session_id: str,
        user_id: str = Depends(user_id_dep),
    ):
        """Delete a conversation and all its files."""
        session = vault.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Check ownership
        if user_id and session.user_id and session.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        success = vault.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete conversation")
        
        return {"success": True, "message": "Conversation deleted"}
    
    # Message endpoints
    @router.post("/{session_id}/messages", response_model=MessageResponse)
    async def add_message(
        session_id: str,
        data: MessageCreate,
        user_id: str = Depends(user_id_dep),
    ):
        """Add a message to a conversation."""
        session = vault.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Check ownership
        if user_id and session.user_id and session.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        message = session.add_message(
            role=data.role,
            content=data.content,
            **(data.metadata or {})
        )
        
        return MessageResponse(
            role=message.role,
            content=message.content,
            timestamp=message.timestamp,
        )
    
    # File endpoints
    @router.post("/{session_id}/files")
    async def upload_file(
        session_id: str,
        file: UploadFile = File(...),
        user_id: str = Depends(user_id_dep),
    ):
        """Upload a file to a conversation."""
        session = vault.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Check ownership
        if user_id and session.user_id and session.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        content = await file.read()
        attachment = session.attach_file(
            filename=file.filename,
            content=content,
            content_type=file.content_type or "application/octet-stream",
        )
        
        return {
            "filename": attachment.filename,
            "size": attachment.size,
            "content_type": attachment.content_type,
            "uploaded_at": attachment.uploaded_at.isoformat(),
        }
    
    @router.get("/{session_id}/files")
    async def list_files(
        session_id: str,
        user_id: str = Depends(user_id_dep),
    ):
        """List all files in a conversation."""
        session = vault.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Check ownership
        if user_id and session.user_id and session.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {
            "files": [f.to_dict() for f in session.get_files()]
        }
    
    @router.get("/{session_id}/files/{filename}")
    async def get_file_url(
        session_id: str,
        filename: str,
        expires_in: int = 3600,
        user_id: str = Depends(user_id_dep),
    ):
        """Get a signed download URL for a file."""
        session = vault.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Check ownership
        if user_id and session.user_id and session.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        url = session.get_file_url(filename, expires_in=expires_in)
        if not url:
            raise HTTPException(status_code=404, detail="File not found")
        
        return {"download_url": url, "expires_in": expires_in}
    
    # Auto-create conversation on first message (convenience endpoint)
    @router.post("/chat")
    async def chat(
        content: str = Form(...),
        session_id: Optional[str] = Form(None),
        files: list[UploadFile] = File(default=[]),
        user_id: str = Depends(user_id_dep),
    ):
        """
        Send a message, auto-creating a conversation if needed.
        
        This is a convenience endpoint that combines:
        1. Create conversation (if session_id not provided)
        2. Upload files (if any)
        3. Add user message
        
        Returns the session_id so the client can continue the conversation.
        """
        # Auto-create conversation if no session_id
        if not session_id:
            session = vault.create_session(user_id=user_id)
        else:
            session = vault.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            # Check ownership
            if user_id and session.user_id and session.user_id != user_id:
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Upload files if any
        uploaded_files = []
        for file in files:
            file_content = await file.read()
            attachment = session.attach_file(
                filename=file.filename,
                content=file_content,
                content_type=file.content_type or "application/octet-stream",
            )
            uploaded_files.append({
                "filename": attachment.filename,
                "size": attachment.size,
            })
        
        # Add user message
        message = session.add_message(role="user", content=content)
        
        return {
            "session_id": session.session_id,
            "title": session.title,
            "message": {
                "role": message.role,
                "content": message.content,
                "timestamp": message.timestamp.isoformat(),
            },
            "files": uploaded_files,
            "is_new_conversation": session_id is None,
        }
    
    return router
