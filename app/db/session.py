"""
app/db/session.py
-----------------
Database engine and session factory setup.

SQLAlchemy 2.x async support requires:
  1. An async engine (create_async_engine) backed by asyncpg for PostgreSQL.
  2. An async session factory (async_sessionmaker) to create sessions per request.
  3. A Base class that all ORM models inherit from, so Alembic can detect them.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# ---------------------------------------------------------------------------
# Declarative Base
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    """
    All SQLAlchemy ORM models inherit from this class.
    It provides the metadata object that Alembic uses for migrations.
    """
    pass


# ---------------------------------------------------------------------------
# Async Engine
# ---------------------------------------------------------------------------
# echo=True logs every SQL statement — useful for debugging, disable in prod.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    # Connection pool size tuning (asyncpg manages its own pool internally)
    pool_pre_ping=True,   # Verify connections before using them (avoids stale conn errors)
    pool_recycle=3600,    # Recycle connections every hour
)


# ---------------------------------------------------------------------------
# Async Session Factory
# ---------------------------------------------------------------------------
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit so we can still read them
    autoflush=False,          # We control when to flush manually
    autocommit=False,         # Always use explicit transactions
)
