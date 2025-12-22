"""
ChatVault UI - Chainlit-based chat interface.

This module provides a ready-to-mount Chainlit chat UI that integrates
with ChatVault for conversation persistence.

Usage:
    from chatvault import ChatVault
    from chatvault.ui import create_chainlit_app
    
    vault = ChatVault(storage=..., persistence=...)
    chainlit_app = create_chainlit_app(vault, message_handler=my_ai_handler)
    
    # Mount on FastAPI
    app.mount("/chat", chainlit_app)

Note: Requires chatvault[ui] optional dependency.
"""

try:
    from chatvault.ui.app import create_chainlit_app
    __all__ = ["create_chainlit_app"]
except ImportError:
    # Chainlit not installed
    def create_chainlit_app(*args, **kwargs):
        raise ImportError(
            "Chainlit is not installed. Install with: pip install chatvault[ui]"
        )
    __all__ = ["create_chainlit_app"]
