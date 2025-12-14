"""
ChatVault API - FastAPI router for conversation management.

This module provides a ready-to-use FastAPI router that apps can mount
to get all conversation management endpoints.

Usage:
    from chatvault import ChatVault
    from chatvault.api import create_router
    
    vault = ChatVault(storage=..., persistence=...)
    app.include_router(create_router(vault), prefix="/api")
"""

from chatvault.api.router import create_router

__all__ = ["create_router"]
