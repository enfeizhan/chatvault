"""
ChatVault - Main vault class.

The ChatVault is the primary interface for managing conversations and files.
"""

from typing import Optional
from chatvault.conversation import Conversation
from chatvault.backends.messages.base import MessagesBackend
from chatvault.backends.files.base import FilesBackend


class ChatVault:
    """
    Main ChatVault class for managing AI conversations.
    
    Example:
        vault = ChatVault(
            messages=MyMessagesBackend(...),
            files=MyFilesBackend(...),
        )
        
        conversation = vault.create_conversation(user_id="user-123")
        conversation.add_message("user", "Hello!")
    """
    
    def __init__(
        self,
        messages: MessagesBackend,
        files: FilesBackend,
    ):
        """
        Initialize ChatVault.
        
        Args:
            messages: Backend for storing conversation data
            files: Backend for storing file attachments
        """
        self._messages = messages
        self._files = files
    
    def create_conversation(self, user_id: Optional[str] = None, **metadata) -> Conversation:
        """
        Create a new conversation.
        
        Args:
            user_id: Optional user ID to associate with the conversation
            **metadata: Additional metadata to store with the conversation
            
        Returns:
            A new Conversation instance
        """
        conversation = Conversation.new(user_id=user_id, metadata=metadata, _vault=self)
        self._messages.save(conversation)
        return conversation
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Load an existing conversation by ID.
        
        Args:
            conversation_id: The conversation ID to load
            
        Returns:
            The Conversation if found, None otherwise
        """
        conversation = self._messages.get(conversation_id)
        if conversation:
            conversation._vault = self
        return conversation
    
    def get_user_conversations(self, user_id: str) -> list[Conversation]:
        """
        Get all conversations for a user.
        
        Args:
            user_id: The user ID to query
            
        Returns:
            List of conversations belonging to the user
        """
        conversations = self._messages.get_by_user(user_id)
        for conversation in conversations:
            conversation._vault = self
        return conversations
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation and its associated files.
        
        Args:
            conversation_id: The conversation ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return False
        
        # Delete files from storage
        for f in conversation.get_files():
            self._files.delete(f.storage_key)
        
        # Delete conversation from messages backend
        return self._messages.delete(conversation_id)
    
    def archive_conversation(self, conversation_id: str) -> bool:
        """
        Archive a conversation (mark as inactive).
        
        Args:
            conversation_id: The conversation ID to archive
            
        Returns:
            True if archived, False if not found
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return False
        
        conversation.metadata["archived"] = True
        self._messages.save(conversation)
        return True
