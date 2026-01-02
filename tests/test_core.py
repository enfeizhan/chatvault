"""Tests for ChatVault core functionality."""

import pytest
from chatvault import ChatVault, Conversation, Message
from chatvault.storage import LocalStorage
from chatvault.persistence import MemoryBackend


@pytest.fixture
def vault(tmp_path):
    """Create a vault with temporary storage."""
    return ChatVault(
        storage=LocalStorage(base_path=str(tmp_path / "uploads")),
        persistence=MemoryBackend()
    )


class TestConversation:
    """Tests for Conversation class."""
    
    def test_create_conversation(self, vault):
        """Test creating a new conversation."""
        conversation = vault.create_conversation(user_id="user-123")
        
        assert conversation.conversation_id is not None
        assert conversation.user_id == "user-123"
        assert conversation.title == ""
        assert len(conversation.get_messages()) == 0
    
    def test_add_messages(self, vault):
        """Test adding messages to a conversation."""
        conversation = vault.create_conversation()
        
        conversation.add_message("user", "Hello!")
        conversation.add_message("assistant", "Hi there!")
        
        messages = conversation.get_messages()
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[0].content == "Hello!"
        assert messages[1].role == "assistant"
    
    def test_auto_title(self, vault):
        """Test auto-generation of title from first user message."""
        conversation = vault.create_conversation()
        
        conversation.add_message("user", "What is the weather today?")
        
        assert conversation.title == "What is the weather today?"
    
    def test_get_history(self, vault):
        """Test getting LLM-compatible history."""
        conversation = vault.create_conversation()
        conversation.add_message("user", "Hello")
        conversation.add_message("assistant", "Hi")
        
        history = conversation.get_history()
        
        assert history == [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ]


class TestFileAttachments:
    """Tests for file attachments."""
    
    def test_attach_file(self, vault):
        """Test attaching a file to a conversation."""
        conversation = vault.create_conversation(user_id="user-123")
        
        content = b"Hello, World!"
        attachment = conversation.attach_file(
            "test.txt",
            content,
            content_type="text/plain"
        )
        
        assert attachment.filename == "test.txt"
        assert attachment.size == len(content)
        assert attachment.content_type == "text/plain"
    
    def test_get_file_content(self, vault):
        """Test retrieving file content."""
        conversation = vault.create_conversation()
        
        original_content = b"Test file content"
        conversation.attach_file("doc.txt", original_content)
        
        retrieved = conversation.get_file_content("doc.txt")
        assert retrieved == original_content
    
    def test_list_files(self, vault):
        """Test listing attached files."""
        conversation = vault.create_conversation()
        
        conversation.attach_file("file1.txt", b"content1")
        conversation.attach_file("file2.pdf", b"content2", content_type="application/pdf")
        
        files = conversation.get_files()
        assert len(files) == 2
        assert files[0].filename == "file1.txt"
        assert files[1].filename == "file2.pdf"


class TestConversationPersistence:
    """Tests for conversation persistence."""
    
    def test_load_conversation(self, vault):
        """Test loading a conversation by ID."""
        conversation = vault.create_conversation(user_id="user-456")
        conversation.add_message("user", "Test message")
        conversation_id = conversation.conversation_id
        
        # Load the conversation
        loaded = vault.get_conversation(conversation_id)
        
        assert loaded is not None
        assert loaded.conversation_id == conversation_id
        assert loaded.user_id == "user-456"
        assert len(loaded.get_messages()) == 1
    
    def test_get_user_conversations(self, vault):
        """Test getting all conversations for a user."""
        vault.create_conversation(user_id="user-A")
        vault.create_conversation(user_id="user-A")
        vault.create_conversation(user_id="user-B")
        
        user_a_conversations = vault.get_user_conversations("user-A")
        
        assert len(user_a_conversations) == 2
        assert all(s.user_id == "user-A" for s in user_a_conversations)
    
    def test_delete_conversation(self, vault):
        """Test deleting a conversation."""
        conversation = vault.create_conversation()
        conversation_id = conversation.conversation_id
        
        result = vault.delete_conversation(conversation_id)
        
        assert result is True
        assert vault.get_conversation(conversation_id) is None
