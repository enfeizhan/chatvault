"""Quick test for ChatVault API router."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatvault import ChatVault
from chatvault.backends import LocalFiles, MemoryMessages
from chatvault.api import create_router


@pytest.fixture
def vault(tmp_path):
    """Create a test vault."""
    return ChatVault(
        messages=MemoryMessages(),
        files=LocalFiles(base_path=str(tmp_path))
    )


@pytest.fixture
def client(vault):
    """Create test client with ChatVault router."""
    app = FastAPI()
    
    # Mock user authentication
    async def get_test_user():
        return "test-user-123"
    
    app.include_router(
        create_router(vault, get_user_id=get_test_user),
        prefix="/api"
    )
    
    return TestClient(app)


def test_create_conversation(client):
    """Test creating a new conversation."""
    response = client.post("/api/conversations", json={"title": "Test Chat"})
    assert response.status_code == 200
    data = response.json()
    assert "conversation_id" in data
    assert data["title"] == "Test Chat"


def test_list_conversations(client):
    """Test listing conversations."""
    # Create a conversation first
    client.post("/api/conversations", json={"title": "Chat 1"})
    client.post("/api/conversations", json={"title": "Chat 2"})
    
    response = client.get("/api/conversations")
    assert response.status_code == 200
    data = response.json()
    assert len(data["conversations"]) == 2


def test_rename_conversation(client):
    """Test renaming a conversation."""
    # Create
    create_resp = client.post("/api/conversations", json={"title": "Original"})
    conversation_id = create_resp.json()["conversation_id"]
    
    # Rename
    response = client.patch(f"/api/conversations/{conversation_id}", json={"title": "Renamed"})
    assert response.status_code == 200
    assert response.json()["title"] == "Renamed"


def test_delete_conversation(client):
    """Test deleting a conversation."""
    # Create
    create_resp = client.post("/api/conversations", json={"title": "To Delete"})
    conversation_id = create_resp.json()["conversation_id"]
    
    # Delete
    response = client.delete(f"/api/conversations/{conversation_id}")
    assert response.status_code == 200
    
    # Verify deleted
    get_resp = client.get(f"/api/conversations/{conversation_id}")
    assert get_resp.status_code == 404


def test_add_message(client):
    """Test adding a message to a conversation."""
    # Create conversation
    create_resp = client.post("/api/conversations")
    conversation_id = create_resp.json()["conversation_id"]
    
    # Add message
    response = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"role": "user", "content": "Hello!"}
    )
    assert response.status_code == 200
    assert response.json()["content"] == "Hello!"


def test_chat_auto_create(client):
    """Test auto-create conversation on first message."""
    response = client.post(
        "/api/conversations/chat",
        data={"content": "This is my first message"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "conversation_id" in data
    assert data["is_new_conversation"] == True
    assert data["message"]["content"] == "This is my first message"
    # Title should be auto-generated from content
    assert data["title"] != ""


def test_chat_existing_conversation(client):
    """Test sending message to existing conversation."""
    # Create first
    first_resp = client.post(
        "/api/conversations/chat",
        data={"content": "First message"}
    )
    conversation_id = first_resp.json()["conversation_id"]
    
    # Continue conversation
    response = client.post(
        "/api/conversations/chat",
        data={"content": "Second message", "conversation_id": conversation_id}
    )
    assert response.status_code == 200
    assert response.json()["conversation_id"] == conversation_id
    assert response.json()["is_new_conversation"] == False
