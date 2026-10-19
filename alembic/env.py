"""
alembic/env.py
--------------
Alembic migration environment configuration.

Alembic is a database migration tool that tracks schema changes over time.
This file tells Alembic:
  1. How to connect to the database.
  2. Which SQLAlchemy models to inspect for schema changes.
  3. How to run migrations (online = against a real DB, offline = generate SQL).

To create a new migration after changing a model:
  alembic revision --autogenerate -m "add column X to table Y"

To apply pending migrations:
  alembic upgrade head
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# --- Import app config and all models ---
# Importing models here ensures Alembic knows about them when autogenerating.
from app.core.config import settings
from app.db.session import Base
import app.models  # noqa: F401 — side-effect import: registers all models with Base.metadata

# Alembic Config object (reads alembic.ini)
config = context.config

# Set database URL from our settings (overrides what's in alembic.ini)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Setup Python logging from alembic.ini [loggers] section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The metadata object that autogenerate inspects to find schema changes
target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Offline mode — generates a .sql file instead of running against a real DB
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Useful when you want to review the SQL before applying it,
    or when you don't have direct DB access (e.g. in CI).
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online mode — runs migrations directly against the database
# ---------------------------------------------------------------------------
def do_run_migrations(connection: Connection) -> None:
    """Execute migrations using the provided connection."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations inside it."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # Don't use connection pooling during migrations
    )

    async with connectable.connect() as connection:
        # run_sync lets us call the sync Alembic API from async code
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online (async) migrations."""
    asyncio.run(run_async_migrations())


# Decide which mode to run based on Alembic context
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
