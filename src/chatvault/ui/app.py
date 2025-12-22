"""
ChatVault Chainlit Application.

Creates a Chainlit-based chat UI that uses ChatVault for persistence.
"""

from typing import Callable, Awaitable, Optional, Any
import logging
import chainlit as cl
from fastapi import FastAPI

from chatvault import ChatVault
from chatvault.session import Session, Message

logger = logging.getLogger(__name__)


def create_chainlit_app(
    vault: ChatVault,
    message_handler: Callable[[str, Session], Awaitable[str]],
    get_user_id: Optional[Callable[[], Awaitable[Optional[str]]]] = None,
    title: str = "ChatVault Assistant",
) -> FastAPI:
    """
    Create a Chainlit FastAPI app wired to ChatVault.
    
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
            
        chainlit_app = create_chainlit_app(vault, my_ai_handler)
        app.mount("/chat", chainlit_app)
    """
    
    # Store config in user session for access in handlers
    @cl.on_chat_start
    async def on_chat_start():
        """Initialize session when chat starts."""
        # Get or create session ID
        session_id = cl.user_session.get("session_id")
        
        if not session_id:
            # Try to get user ID for session linking
            user_id = None
            if get_user_id:
                try:
                    user_id = await get_user_id()
                except Exception:
                    pass
            
            # Create new ChatVault session
            session = vault.create_session(user_id=user_id)
            session_id = session.session_id
            cl.user_session.set("session_id", session_id)
            logger.info(f"Created new session: {session_id}")
        else:
            logger.info(f"Resuming session: {session_id}")
        
        # Store references
        cl.user_session.set("vault", vault)
        cl.user_session.set("message_handler", message_handler)
        
        # Send welcome message
        await cl.Message(
            content=f"👋 Welcome! I'm ready to help.",
            author="assistant"
        ).send()
    
    @cl.on_message
    async def on_message(message: cl.Message):
        """Handle incoming user messages."""
        vault_instance: ChatVault = cl.user_session.get("vault")
        handler = cl.user_session.get("message_handler")
        session_id = cl.user_session.get("session_id")
        
        if not all([vault_instance, handler, session_id]):
            await cl.Message(content="Session error. Please refresh.").send()
            return
        
        # Get session
        session = vault_instance.get_session(session_id)
        if not session:
            session = vault_instance.create_session()
            session_id = session.session_id
            cl.user_session.set("session_id", session_id)
        
        # Add user message to session
        session.add_message(Message(role="user", content=message.content))
        
        # Show thinking indicator
        msg = cl.Message(content="")
        await msg.send()
        
        try:
            # Call the AI handler
            response = await handler(message.content, session)
            
            # Add assistant response to session
            session.add_message(Message(role="assistant", content=response))
            
            # Save session
            vault_instance.save_session(session)
            
            # Update the message with response
            msg.content = response
            await msg.update()
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            msg.content = f"Sorry, an error occurred: {str(e)}"
            await msg.update()
    
    @cl.on_chat_end
    async def on_chat_end():
        """Clean up when chat ends."""
        session_id = cl.user_session.get("session_id")
        if session_id:
            logger.info(f"Chat ended for session: {session_id}")
    
    # Return the Chainlit FastAPI app
    from chainlit.server import app as chainlit_fastapi_app
    return chainlit_fastapi_app
