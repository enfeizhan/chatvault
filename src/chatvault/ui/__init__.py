"""
ChatVault UI - Chat interface for AI conversations.

This module provides a ready-to-mount chat UI that integrates
with ChatVault for conversation persistence.

Usage:
    from chatvault import ChatVault
    from chatvault.ui import create_chatvault_app
    
    vault = ChatVault(storage=..., persistence=...)
    chat_app = create_chatvault_app(vault, message_handler=my_ai_handler)
    
    # Mount on FastAPI
    app.mount("/chat", chat_app)

Note: Requires chatvault[ui] optional dependency.
"""

try:
    from chatvault.ui.app import create_chatvault_app
    __all__ = ["create_chatvault_app"]
except ImportError:
    # UI dependencies not installed
    def create_chatvault_app(*args, **kwargs):
        raise ImportError(
            "UI dependencies not installed. Install with: pip install chatvault[ui]"
        )
    __all__ = ["create_chatvault_app"]
