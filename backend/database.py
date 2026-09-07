"""
Database configuration and session management for LegalLens (Phase 7).
Configures SQLAlchemy engine, declarative Base, and session generator.
Supports PostgreSQL (psycopg2) and SQLite fallback for local testing.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Determine database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./backend/legallens_dev.db")
SQLITE_FALLBACK_URL = os.getenv("SQLITE_FALLBACK_URL", "sqlite:///./backend/legallens_dev.db")

# In testing or when PostgreSQL is unreachable locally, fall back to SQLite cleanly
connect_args = {}
if "sqlite" in DATABASE_URL:
    connect_args = {"check_same_thread": False}

try:
    engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
    # Quick probe
    with engine.connect() as conn:
        pass
except Exception:
    # Fallback to local SQLite if PostgreSQL service is not actively running
    DATABASE_URL = SQLITE_FALLBACK_URL
    connect_args = {"check_same_thread": False}
    engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency for obtaining a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initializes all registered database tables."""
    import backend.models  # Ensure all models are registered with Base
    Base.metadata.create_all(bind=engine)
