"""
Backward compatibility module.
All canonical database connections, engine, and Base reside in app.database.db.
"""

from app.database.db import (
    DATABASE_URL,
    Base,
    SessionLocal,
    engine,
    get_db,
)

__all__ = [
    "DATABASE_URL",
    "engine",
    "SessionLocal",
    "Base",
    "get_db",
]
