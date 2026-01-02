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
    conversation_id: str
    title: str
    created_at: datetime
    last_active: datetime
    message_count: int
    file_count: int


class ConversationDetail(BaseModel):
    """Full conversation details."""
    conversation_id: str
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
        vault = ChatVault(messages=..., files=...)
        
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
    
    @router.get("")
    async def list_conversations(
        user_id: str = Depends(user_id_dep),
        conversation_id: Optional[str] = None,  # Allow passing conversation_id as query param
    ):
        """
        List conversations for the current user.
        
        For authenticated users: returns all their conversations.
        For anonymous users: returns the current conversation if conversation_id is provided.
        
        Always includes the current conversation_id if provided.
        """
        conversations = []
        conversation_ids_seen = set()
        
        # If user is authenticated, get all their conversations
        if user_id:
            user_conversations = vault.get_user_conversations(user_id)
            for s in user_conversations:
                conversations.append(s)
                conversation_ids_seen.add(s.conversation_id)
        
        # Always try to get the current conversation_id if provided (even for logged-in users)
        # This ensures the current conversation is always visible
        if conversation_id and conversation_id not in conversation_ids_seen:
            conversation = vault.get_conversation(conversation_id)
            if conversation:
                conversations.insert(0, conversation)  # Put current conversation first
        
        # Sort by last_active (most recent first)
        conversations.sort(key=lambda s: s.last_active, reverse=True)
        
        # Return formatted response (compatible with frontend expecting 'conversations' key)
        return {
            "conversations": [
                {
                    "conversation_id": s.conversation_id,
                    "title": s.title or "新对话",
                    "created_at": s.created_at.isoformat(),
                    "last_active": s.last_active.isoformat(),
                    "message_count": len(s._messages),
                    "document_count": len(s._files),
                }
                for s in conversations
            ]
        }
    
    @router.post("", response_model=ConversationDetail)
    async def create_conversation(
        data: Optional[ConversationCreate] = None,
        user_id: str = Depends(user_id_dep),
    ):
        """Create a new conversation."""
        metadata = (data.metadata if data and data.metadata else {}) or {}
        conversation = vault.create_conversation(user_id=user_id, **metadata)
        
        if data and data.title:
            conversation.rename(data.title)
        
        return ConversationDetail(
            conversation_id=conversation.conversation_id,
            user_id=conversation.user_id,
            title=conversation.title,
            created_at=conversation.created_at,
            last_active=conversation.last_active,
            messages=[],
            files=[],
            metadata=conversation.metadata,
        )
    
    @router.get("/{conversation_id}", response_model=ConversationDetail)
    async def get_conversation(
        conversation_id: str,
        user_id: str = Depends(user_id_dep),
    ):
        """Get a conversation by ID."""
        conversation = vault.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Check ownership if user_id is available
        if user_id and conversation.user_id and conversation.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return ConversationDetail(
            conversation_id=conversation.conversation_id,
            user_id=conversation.user_id,
            title=conversation.title,
            created_at=conversation.created_at,
            last_active=conversation.last_active,
            messages=[m.to_dict() for m in conversation._messages],
            files=[f.to_dict() for f in conversation._files],
            metadata=conversation.metadata,
        )
    
    @router.patch("/{conversation_id}", response_model=ConversationDetail)
    async def update_conversation(
        conversation_id: str,
        data: ConversationUpdate,
        user_id: str = Depends(user_id_dep),
    ):
        """Update a conversation (rename, update metadata)."""
        conversation = vault.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Check ownership
        if user_id and conversation.user_id and conversation.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if data.title is not None:
            conversation.rename(data.title)
        
        if data.metadata is not None:
            conversation.metadata.update(data.metadata)
            conversation._save()
        
        return ConversationDetail(
            conversation_id=conversation.conversation_id,
            user_id=conversation.user_id,
            title=conversation.title,
            created_at=conversation.created_at,
            last_active=conversation.last_active,
            messages=[m.to_dict() for m in conversation._messages],
            files=[f.to_dict() for f in conversation._files],
            metadata=conversation.metadata,
        )
    
    @router.delete("/{conversation_id}")
    async def delete_conversation(
        conversation_id: str,
        user_id: str = Depends(user_id_dep),
    ):
        """Delete a conversation and all its files."""
        conversation = vault.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Check ownership
        if user_id and conversation.user_id and conversation.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        success = vault.delete_conversation(conversation_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete conversation")
        
        return {"success": True, "message": "Conversation deleted"}
    
    # Message endpoints
    @router.post("/{conversation_id}/messages", response_model=MessageResponse)
    async def add_message(
        conversation_id: str,
        data: MessageCreate,
        user_id: str = Depends(user_id_dep),
    ):
        """Add a message to a conversation."""
        conversation = vault.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Check ownership
        if user_id and conversation.user_id and conversation.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        message = conversation.add_message(
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
    @router.post("/{conversation_id}/files")
    async def upload_file(
        conversation_id: str,
        file: UploadFile = File(...),
        user_id: str = Depends(user_id_dep),
    ):
        """Upload a file to a conversation."""
        conversation = vault.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Check ownership
        if user_id and conversation.user_id and conversation.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        content = await file.read()
        attachment = conversation.attach_file(
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
    
    @router.get("/{conversation_id}/files")
    async def list_files(
        conversation_id: str,
        user_id: str = Depends(user_id_dep),
    ):
        """List all files in a conversation."""
        conversation = vault.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Check ownership
        if user_id and conversation.user_id and conversation.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {
            "files": [f.to_dict() for f in conversation.get_files()]
        }
    
    @router.get("/{conversation_id}/files/{filename}")
    async def get_file_url(
        conversation_id: str,
        filename: str,
        expires_in: int = 3600,
        user_id: str = Depends(user_id_dep),
    ):
        """Get a signed download URL for a file."""
        conversation = vault.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Check ownership
        if user_id and conversation.user_id and conversation.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        url = conversation.get_file_url(filename, expires_in=expires_in)
        if not url:
            raise HTTPException(status_code=404, detail="File not found")
        
        return {"download_url": url, "expires_in": expires_in}
    
    @router.delete("/{conversation_id}/files/{filename}")
    async def delete_file(
        conversation_id: str,
        filename: str,
        user_id: str = Depends(user_id_dep),
    ):
        """Delete a file from a conversation."""
        conversation = vault.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Check ownership - only owner can delete files
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")
        if conversation.user_id and conversation.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Find the file to get its storage_key
        file_to_delete = None
        for f in conversation._files:
            if f.filename == filename:
                file_to_delete = f
                break
        
        if not file_to_delete:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Delete from storage backend
        if conversation._vault and conversation._vault._files:
            try:
                conversation._vault._files.delete(file_to_delete.storage_key)
            except Exception as e:
                # Log but continue - metadata cleanup is more important
                pass
        
        # Remove from conversation metadata
        conversation._files = [f for f in conversation._files if f.filename != filename]
        conversation._save()
        return {"success": True, "message": "File deleted"}
    
    # Auto-create conversation on first message (convenience endpoint)
    @router.post("/chat")
    async def chat(
        content: str = Form(...),
        conversation_id: Optional[str] = Form(None),
        files: list[UploadFile] = File(default=[]),
        user_id: str = Depends(user_id_dep),
    ):
        """
        Send a message, auto-creating a conversation if needed.
        
        This is a convenience endpoint that combines:
        1. Create conversation (if conversation_id not provided)
        2. Upload files (if any)
        3. Add user message
        
        Returns the conversation_id so the client can continue the conversation.
        """
        # Auto-create conversation if no conversation_id
        if not conversation_id:
            conversation = vault.create_conversation(user_id=user_id)
        else:
            conversation = vault.get_conversation(conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            # Check ownership
            if user_id and conversation.user_id and conversation.user_id != user_id:
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Upload files if any
        uploaded_files = []
        for file in files:
            file_content = await file.read()
            attachment = conversation.attach_file(
                filename=file.filename,
                content=file_content,
                content_type=file.content_type or "application/octet-stream",
            )
            uploaded_files.append({
                "filename": attachment.filename,
                "size": attachment.size,
            })
        
        # Add user message
        message = conversation.add_message(role="user", content=content)
        
        return {
            "conversation_id": conversation.conversation_id,
            "title": conversation.title,
            "message": {
                "role": message.role,
                "content": message.content,
                "timestamp": message.timestamp.isoformat(),
            },
            "files": uploaded_files,
            "is_new_conversation": conversation_id is None,
        }
    
    return router
