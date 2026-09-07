"""
Database re-export proxy for backward compatibility.
"""

from backend.database import engine, SessionLocal, Base, get_db, init_db

__all__ = ["engine", "SessionLocal", "Base", "get_db", "init_db"]
