"""Tests for ChatVault core functionality."""

import pytest
from chatvault import ChatVault, Session, Message
from chatvault.storage import LocalStorage
from chatvault.persistence import MemoryBackend


@pytest.fixture
def vault(tmp_path):
    """Create a vault with temporary storage."""
    return ChatVault(
        storage=LocalStorage(base_path=str(tmp_path / "uploads")),
        persistence=MemoryBackend()
    )


class TestSession:
    """Tests for Session class."""
    
    def test_create_session(self, vault):
        """Test creating a new session."""
        session = vault.create_session(user_id="user-123")
        
        assert session.session_id is not None
        assert session.user_id == "user-123"
        assert session.title == ""
        assert len(session.get_messages()) == 0
    
    def test_add_messages(self, vault):
        """Test adding messages to a session."""
        session = vault.create_session()
        
        session.add_message("user", "Hello!")
        session.add_message("assistant", "Hi there!")
        
        messages = session.get_messages()
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[0].content == "Hello!"
        assert messages[1].role == "assistant"
    
    def test_auto_title(self, vault):
        """Test auto-generation of title from first user message."""
        session = vault.create_session()
        
        session.add_message("user", "What is the weather today?")
        
        assert session.title == "What is the weather today?"
    
    def test_get_history(self, vault):
        """Test getting LLM-compatible history."""
        session = vault.create_session()
        session.add_message("user", "Hello")
        session.add_message("assistant", "Hi!")
        
        history = session.get_history()
        
        assert history == [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
        ]


class TestFileAttachments:
    """Tests for file attachments."""
    
    def test_attach_file(self, vault):
        """Test attaching a file to a session."""
        session = vault.create_session(user_id="user-123")
        
        content = b"Hello, World!"
        attachment = session.attach_file(
            "test.txt",
            content,
            content_type="text/plain"
        )
        
        assert attachment.filename == "test.txt"
        assert attachment.size == len(content)
        assert attachment.content_type == "text/plain"
    
    def test_get_file_content(self, vault):
        """Test retrieving file content."""
        session = vault.create_session()
        
        original_content = b"Test file content"
        session.attach_file("doc.txt", original_content)
        
        retrieved = session.get_file_content("doc.txt")
        assert retrieved == original_content
    
    def test_list_files(self, vault):
        """Test listing attached files."""
        session = vault.create_session()
        
        session.attach_file("file1.txt", b"content1")
        session.attach_file("file2.pdf", b"content2", content_type="application/pdf")
        
        files = session.get_files()
        assert len(files) == 2
        assert files[0].filename == "file1.txt"
        assert files[1].filename == "file2.pdf"


class TestSessionPersistence:
    """Tests for session persistence."""
    
    def test_load_session(self, vault):
        """Test loading a session by ID."""
        session = vault.create_session(user_id="user-456")
        session.add_message("user", "Test message")
        session_id = session.session_id
        
        # Load the session
        loaded = vault.get_session(session_id)
        
        assert loaded is not None
        assert loaded.session_id == session_id
        assert loaded.user_id == "user-456"
        assert len(loaded.get_messages()) == 1
    
    def test_get_user_sessions(self, vault):
        """Test getting all sessions for a user."""
        vault.create_session(user_id="user-A")
        vault.create_session(user_id="user-A")
        vault.create_session(user_id="user-B")
        
        user_a_sessions = vault.get_user_sessions("user-A")
        
        assert len(user_a_sessions) == 2
        assert all(s.user_id == "user-A" for s in user_a_sessions)
    
    def test_delete_session(self, vault):
        """Test deleting a session."""
        session = vault.create_session()
        session_id = session.session_id
        
        result = vault.delete_session(session_id)
        
        assert result is True
        assert vault.get_session(session_id) is None
