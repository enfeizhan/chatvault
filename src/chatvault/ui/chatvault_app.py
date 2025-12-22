"""
ChatVault Chainlit App - Standalone Chainlit app file for mount_chainlit.

This file is used by mount_chainlit to properly mount the Chainlit UI.
It retrieves configuration from the _chatvault_config registry.
"""

import chainlit as cl
import logging

from chatvault.session import Message

logger = logging.getLogger(__name__)

# Global registry for ChatVault configuration
# Set by mount_chatvault_ui() before mounting
_chatvault_config = {
    "vault": None,
    "message_handler": None,
    "get_user_id": None,
    "title": "ChatVault Assistant"
}


def configure(vault, message_handler, get_user_id=None, title="ChatVault Assistant"):
    """Configure the ChatVault app with required dependencies.
    
    Called by mount_chatvault_ui() before mounting.
    """
    _chatvault_config["vault"] = vault
    _chatvault_config["message_handler"] = message_handler
    _chatvault_config["get_user_id"] = get_user_id
    _chatvault_config["title"] = title


@cl.on_chat_start
async def on_chat_start():
    """Initialize session when chat starts."""
    vault = _chatvault_config["vault"]
    message_handler = _chatvault_config["message_handler"]
    get_user_id = _chatvault_config["get_user_id"]
    
    if not vault or not message_handler:
        await cl.Message(
            content="❌ ChatVault not configured. Please check server logs.",
            author="system"
        ).send()
        return
    
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
    
    # Store references in user session
    cl.user_session.set("vault", vault)
    cl.user_session.set("message_handler", message_handler)
    
    # Send welcome message
    await cl.Message(
        content="👋 Welcome! I'm ready to help.",
        author="assistant"
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming user messages."""
    vault_instance = cl.user_session.get("vault")
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
