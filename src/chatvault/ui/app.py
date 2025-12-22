"""
ChatVault UI Application.

Creates a chat UI that uses ChatVault for persistence.
"""

from typing import Callable, Awaitable, Optional
import logging
import os
import warnings

from fastapi import FastAPI

from chatvault import ChatVault
from chatvault.session import Session

logger = logging.getLogger(__name__)


def mount_chatvault_ui(
    app: FastAPI,
    vault: ChatVault,
    message_handler: Callable[[str, Session], Awaitable[str]],
    path: str = "/chat",
    get_user_id: Optional[Callable[[], Awaitable[Optional[str]]]] = None,
    title: str = "ChatVault Assistant",
) -> None:
    """
    Mount ChatVault chat UI on a FastAPI app at the specified path.
    
    This function properly handles Chainlit's path routing by using
    mount_chainlit internally.
    
    Args:
        app: Parent FastAPI application
        vault: ChatVault instance for persistence
        message_handler: Async function that takes (user_message, session) and returns AI response
        path: URL path to mount the chat UI (default: "/chat")
        get_user_id: Optional async function to get current user ID (for auth integration)
        title: Chat window title
        
    Example:
        from chatvault.ui import mount_chatvault_ui
        
        async def my_ai_handler(message: str, session: Session) -> str:
            return await my_llm.chat(message)
            
        mount_chatvault_ui(app, vault, my_ai_handler, path="/chat")
    """
    from chainlit.utils import mount_chainlit
    
    # Configure the chainlit app with our dependencies
    from chatvault.ui.chatvault_app import configure
    configure(vault, message_handler, get_user_id, title)
    
    # Get the path to the chatvault_app.py file
    chatvault_app_path = os.path.join(
        os.path.dirname(__file__), 
        "chatvault_app.py"
    )
    
    # Mount using Chainlit's utility which handles path routing correctly
    mount_chainlit(app=app, target=chatvault_app_path, path=path)
    
    logger.info(f"ChatVault UI mounted at {path}")


def create_chatvault_app(
    vault: ChatVault,
    message_handler: Callable[[str, Session], Awaitable[str]],
    get_user_id: Optional[Callable[[], Awaitable[Optional[str]]]] = None,
    title: str = "ChatVault Assistant",
) -> FastAPI:
    """
    Create a ChatVault chat UI application.
    
    .. deprecated::
        Use `mount_chatvault_ui()` instead for proper path handling.
        This function returns a FastAPI app that may not work correctly
        when mounted at non-root paths.
    
    Args:
        vault: ChatVault instance for persistence
        message_handler: Async function that takes (user_message, session) and returns AI response
        get_user_id: Optional async function to get current user ID (for auth integration)
        title: Chat window title
        
    Returns:
        FastAPI app that can be mounted on your main app
        
    Example:
        async def my_ai_handler(message: str, session: Session) -> str:
            return await my_llm.chat(message)
            
        chat_app = create_chatvault_app(vault, my_ai_handler)
        app.mount("/chat", chat_app)
    """
    warnings.warn(
        "create_chatvault_app() is deprecated and may not work correctly when "
        "mounted at non-root paths. Use mount_chatvault_ui() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Configure the chainlit app
    from chatvault.ui.chatvault_app import configure
    configure(vault, message_handler, get_user_id, title)
    
    # Return the Chainlit FastAPI app (may not work at non-root paths)
    from chainlit.server import app as chainlit_fastapi_app
    return chainlit_fastapi_app
