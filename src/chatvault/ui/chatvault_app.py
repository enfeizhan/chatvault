"""
ChatVault Chainlit App - Standalone Chainlit app file for mount_chainlit.

This file is used by mount_chainlit to properly mount the Chainlit UI.
It retrieves configuration from the shared config module.
"""

import chainlit as cl
import logging
import sys

logger = logging.getLogger(__name__)


def _get_config():
    """Get config from the shared module, handling various import scenarios."""
    # Try multiple import paths to find the already-configured module
    for module_name in ['chatvault.ui.config', 'config']:
        if module_name in sys.modules:
            config_module = sys.modules[module_name]
            if hasattr(config_module, 'get_config'):
                return config_module.get_config()
    
    # Fallback: direct import
    try:
        from chatvault.ui.config import get_config
        return get_config()
    except ImportError:
        pass
    
    return {"vault": None, "message_handler": None, "get_user_id": None, "title": "ChatVault Assistant"}


@cl.on_chat_start
async def on_chat_start():
    """Initialize session when chat starts."""
    config = _get_config()
    vault = config.get("vault")
    message_handler = config.get("message_handler")
    get_user_id = config.get("get_user_id")
    
    logger.info(f"on_chat_start: vault={vault is not None}, handler={message_handler is not None}")
    
    if not vault or not message_handler:
        await cl.Message(
            content="❌ ChatVault not configured. Please check server logs.",
            author="system"
        ).send()
        logger.error("ChatVault config missing: vault or message_handler is None")
        return
    
    # Get or create session ID
    session_id = cl.user_session.get("session_id")
    
    if not session_id:
        # Try to get user ID for session linking
        user_id = None
        if get_user_id:
            try:
                user_id = await get_user_id()
            except Exception as e:
                logger.warning(f"Failed to get user_id: {e}")
        
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
    from chatvault.session import Message
    
    vault_instance = cl.user_session.get("vault")
    handler = cl.user_session.get("message_handler")
    session_id = cl.user_session.get("session_id")
    
    if not all([vault_instance, handler, session_id]):
        logger.error(f"Session error: vault={vault_instance is not None}, handler={handler is not None}, session_id={session_id}")
        await cl.Message(content="Session error. Please refresh.").send()
        return
    
    # Get session
    session = vault_instance.get_session(session_id)
    if not session:
        session = vault_instance.create_session()
        session_id = session.session_id
        cl.user_session.set("session_id", session_id)
    
    # Add user message to session
    session.add_message("user", message.content)
    
    # Show thinking indicator
    msg = cl.Message(content="")
    await msg.send()
    
    try:
        # Call the AI handler
        response = await handler(message.content, session)
        
        # Add assistant response to session
        session.add_message("assistant", response)
        
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
