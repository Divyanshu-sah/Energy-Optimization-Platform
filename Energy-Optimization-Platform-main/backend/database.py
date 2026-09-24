"""
Database connection and session management for EnergiX Copilot
Lazy initialization — PostgreSQL is optional, falls back gracefully
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:energix123@localhost:5432/energix_db"
)

_engine = None
_SessionLocal = None
_db_available = False


def _get_engine():
    global _engine, _db_available
    if _engine is None:
        try:
            _engine = create_engine(
                DATABASE_URL, pool_pre_ping=True, pool_size=5, max_overflow=10
            )
            with _engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            _db_available = True
        except Exception:
            _db_available = False
            _engine = None
    return _engine


def get_session_factory():
    global _SessionLocal
    engine = _get_engine()
    if engine is None:
        return None
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionLocal


def is_db_available():
    _get_engine()
    return _db_available


def init_db():
    engine = _get_engine()
    if engine is None:
        print("⚠️ PostgreSQL not available, skipping DB init")
        return False
    try:
        from db_models import Base

        Base.metadata.create_all(bind=engine)
        print("✅ Database tables initialized")
        return True
    except Exception as e:
        print(f"⚠️ DB init failed: {e}")
        return False


@contextmanager
def get_db_session() -> Session:
    factory = get_session_factory()
    if factory is None:
        raise RuntimeError("PostgreSQL not available")
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db():
    factory = get_session_factory()
    if factory is None:
        yield None
        return
    session = factory()
    try:
        yield session
    finally:
        session.close()
