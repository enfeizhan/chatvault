"""
ChatVault Config Registry - Shared configuration for Chainlit app.

Uses a module-level singleton pattern with deferred import to ensure
the same config dict is used regardless of how modules are loaded.
"""

# Global config registry - singleton pattern
_config = None


def get_config():
    """Get the global config dict (singleton)."""
    global _config
    if _config is None:
        _config = {
            "vault": None,
            "message_handler": None,
            "get_user_id": None,
            "title": "ChatVault Assistant"
        }
    return _config


def configure(vault, message_handler, get_user_id=None, title="ChatVault Assistant"):
    """Configure the ChatVault app with required dependencies."""
    config = get_config()
    config["vault"] = vault
    config["message_handler"] = message_handler
    config["get_user_id"] = get_user_id
    config["title"] = title
