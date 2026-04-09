"""
Async SQLAlchemy engine and session factory.

We use asyncpg as the driver because it is significantly faster than
psycopg2 for high-concurrency workloads. pool_pre_ping prevents silent
connection drops from the server-side idle timeout.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

# expire_on_commit=False keeps ORM objects usable after a commit without
# triggering another SELECT to reload them. Useful when returning the object
# immediately after saving.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
