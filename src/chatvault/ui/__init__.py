"""
ChatVault UI - Chat interface for AI conversations.

This module provides a ready-to-mount chat UI that integrates
with ChatVault for conversation persistence.

Usage:
    from chatvault import ChatVault
    from chatvault.ui import mount_chatvault_ui
    
    vault = ChatVault(storage=..., persistence=...)
    
    # Mount on FastAPI (recommended)
    mount_chatvault_ui(app, vault, message_handler=my_ai_handler, path="/chat")

Note: Requires chatvault[ui] optional dependency.
"""

try:
    from chatvault.ui.app import mount_chatvault_ui, create_chatvault_app
    __all__ = ["mount_chatvault_ui", "create_chatvault_app"]
except ImportError:
    # UI dependencies not installed
    def mount_chatvault_ui(*args, **kwargs):
        raise ImportError(
            "UI dependencies not installed. Install with: pip install chatvault[ui]"
        )
    
    def create_chatvault_app(*args, **kwargs):
        raise ImportError(
            "UI dependencies not installed. Install with: pip install chatvault[ui]"
        )
    __all__ = ["mount_chatvault_ui", "create_chatvault_app"]
