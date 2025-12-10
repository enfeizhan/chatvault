# ChatVault

> **Vault your conversations. Unlock your context.**

An open-source Python library for managing AI chat sessions with file attachments and cloud storage.

## Features

- 🗂️ **Session Management** - Create, load, resume, and archive conversations
- 💬 **Message History** - Store and retrieve chat messages with metadata
- 📎 **File Attachments** - Attach files to conversations with cloud storage
- 🔐 **Secure URLs** - Generate signed URLs for file downloads
- 🔌 **Pluggable Backends** - Support for multiple storage and persistence options

## Installation

```bash
pip install chatvault

# With optional backends
pip install chatvault[s3]       # AWS S3 storage
pip install chatvault[oss]      # Alibaba OSS storage
pip install chatvault[postgres] # PostgreSQL persistence
pip install chatvault[redis]    # Redis persistence
pip install chatvault[all]      # All backends
```

## Quick Start

```python
from chatvault import ChatVault
from chatvault.storage import LocalStorage
from chatvault.persistence import MemoryBackend

# Create vault with local storage and in-memory persistence
vault = ChatVault(
    storage=LocalStorage(base_path="./uploads"),
    persistence=MemoryBackend()
)

# Create a new session
session = vault.create_session(user_id="user-123")

# Add messages
session.add_message("user", "Hello!")
session.add_message("assistant", "Hi there! How can I help you?")

# Attach a file
with open("document.pdf", "rb") as f:
    session.attach_file("document.pdf", f.read(), content_type="application/pdf")

# Get conversation history
messages = session.get_messages()

# Resume session later
session = vault.get_session(session.session_id)
```

## Storage Backends

| Backend | Install | Description |
|---------|---------|-------------|
| `LocalStorage` | Built-in | Local filesystem |
| `S3Storage` | `chatvault[s3]` | AWS S3 |
| `OSSStorage` | `chatvault[oss]` | Alibaba Cloud OSS |

## Persistence Backends

| Backend | Install | Description |
|---------|---------|-------------|
| `MemoryBackend` | Built-in | In-memory (for testing) |
| `PostgresBackend` | `chatvault[postgres]` | PostgreSQL |
| `RedisBackend` | `chatvault[redis]` | Redis |

## License

MIT License - see [LICENSE](LICENSE) for details.
