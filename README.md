# ChatVault

> **Vault your conversations. Unlock your context.**

A lightweight Python library for managing AI chat conversations with file attachments. Bring your own storage backends.

## Features

- 🗂️ **Conversation Management** - Create, load, resume, and archive conversations
- 💬 **Message History** - Store and retrieve chat messages with metadata
- 📎 **File Attachments** - Attach files to conversations
- 🔌 **Pluggable Backends** - Implement your own storage for any cloud provider
- 🚀 **FastAPI Integration** - Pre-built API router for instant REST endpoints

## Installation

**Requires Python 3.10+**

```bash
pip install chatvault
```

## Quick Start

```python
from chatvault import ChatVault
from chatvault.backends import MemoryMessages, LocalFiles

# Create vault with built-in backends (great for development)
vault = ChatVault(
    messages=MemoryMessages(),
    files=LocalFiles(base_path="./uploads")
)

# Create a conversation
conversation = vault.create_conversation(user_id="user-123")

# Add messages
conversation.add_message("user", "Hello!")
conversation.add_message("assistant", "Hi there! How can I help you?")

# Attach a file
with open("document.pdf", "rb") as f:
    conversation.attach_file("document.pdf", f.read(), content_type="application/pdf")

# Resume later
conversation = vault.get_conversation(conversation.conversation_id)
```

## FastAPI Integration

ChatVault includes a pre-built FastAPI router for instant REST API:

```python
from fastapi import FastAPI
from chatvault import ChatVault
from chatvault.api import create_router
from chatvault.backends import MemoryMessages, LocalFiles

app = FastAPI()

vault = ChatVault(
    messages=MemoryMessages(),
    files=LocalFiles(base_path="./uploads")
)

# Add all conversation endpoints under /api
app.include_router(create_router(vault), prefix="/api")
```

This gives you these endpoints out of the box:
- `POST /api/conversations` - Create conversation
- `GET /api/conversations` - List conversations
- `GET /api/conversations/{id}` - Get conversation
- `PATCH /api/conversations/{id}` - Rename conversation
- `DELETE /api/conversations/{id}` - Delete conversation
- `POST /api/conversations/{id}/messages` - Add message
- `POST /api/conversations/{id}/files` - Upload file
- `GET /api/conversations/{id}/files/{filename}` - Download file

## API Reference

### ChatVault

| Method | Description |
|--------|-------------|
| `create_conversation(user_id=None)` | Create a new conversation |
| `get_conversation(conversation_id)` | Load an existing conversation |
| `get_conversations(user_id)` | List all conversations for a user |
| `delete_conversation(conversation_id)` | Delete a conversation |

### Conversation

| Method | Description |
|--------|-------------|
| `add_message(role, content)` | Add a message to the conversation |
| `get_messages()` | Get all messages |
| `attach_file(filename, data, content_type)` | Attach a file |
| `get_file(filename)` | Get file content |
| `list_files()` | List all attached files |

## Built-in Backends

| Backend | Description |
|---------|-------------|
| `MemoryMessages` | In-memory storage (for development/testing) |
| `LocalFiles` | Local filesystem storage |

## Custom Backends

ChatVault works with any storage provider. Implement these abstract base classes:

- `MessagesBackend` - For conversation persistence (save, get, get_by_user, delete)
- `FilesBackend` - For file storage (upload, download, delete, exists, get_signed_url)

### Example: AWS S3 + DynamoDB

```python
import boto3
from chatvault.backends import FilesBackend

class S3Files(FilesBackend):
    def __init__(self, bucket: str, region_name: str = None):
        self.bucket = bucket
        self.s3 = boto3.client("s3", region_name=region_name)
    
    def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        self.s3.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)
    
    def download(self, key: str):
        response = self.s3.get_object(Bucket=self.bucket, Key=key)
        return response["Body"].read()
    
    def delete(self, key: str) -> bool:
        self.s3.delete_object(Bucket=self.bucket, Key=key)
        return True
    
    def exists(self, key: str) -> bool:
        try:
            self.s3.head_object(Bucket=self.bucket, Key=key)
            return True
        except:
            return False
    
    def get_signed_url(self, key: str, expires_in: int = 3600, download_filename: str = None):
        return self.s3.generate_presigned_url("get_object", Params={"Bucket": self.bucket, "Key": key}, ExpiresIn=expires_in)
```

```python
import json
from datetime import datetime
import boto3
from chatvault.backends import MessagesBackend
from chatvault.conversation import Conversation, Message, FileAttachment

class DynamoMessages(MessagesBackend):
    def __init__(self, table_name: str, region_name: str = None):
        self.table = boto3.resource("dynamodb", region_name=region_name).Table(table_name)
    
    def save(self, conversation) -> None:
        self.table.put_item(Item={
            "conversation_id": conversation.conversation_id,
            "user_id": conversation.user_id or "",
            "title": conversation.title,
            "messages": json.dumps([m.to_dict() for m in conversation._messages]),
            "files": json.dumps([f.to_dict() for f in conversation._files]),
            "created_at": int(conversation.created_at.timestamp()),
            "last_active": int(conversation.last_active.timestamp()),
        })
    
    def get(self, conversation_id: str):
        response = self.table.get_item(Key={"conversation_id": conversation_id})
        item = response.get("Item")
        if not item:
            return None
        return Conversation(
            conversation_id=item["conversation_id"],
            user_id=item.get("user_id") or None,
            title=item.get("title", ""),
            created_at=datetime.fromtimestamp(int(item.get("created_at", 0))),
            messages=[Message.from_dict(m) for m in json.loads(item.get("messages", "[]"))],
            files=[FileAttachment.from_dict(f) for f in json.loads(item.get("files", "[]"))],
        )
    
    def get_by_user(self, user_id: str):
        response = self.table.query(
            IndexName="user_id-index",
            KeyConditionExpression="user_id = :uid",
            ExpressionAttributeValues={":uid": user_id}
        )
        return [self.get(item["conversation_id"]) for item in response.get("Items", [])]
    
    def delete(self, conversation_id: str) -> bool:
        self.table.delete_item(Key={"conversation_id": conversation_id})
        return True
```

**Usage:**

```python
vault = ChatVault(
    messages=DynamoMessages(table_name="Conversations", region_name="us-east-1"),
    files=S3Files(bucket="my-chat-files", region_name="us-east-1")
)
```

## Development

```bash
# Clone and install
git clone https://github.com/enfeizhan/chatvault.git
cd chatvault
uv venv .venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Run tests
pytest -v
```

## License

MIT License - see [LICENSE](LICENSE) for details.
