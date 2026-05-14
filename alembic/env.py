from logging.config import fileConfig

from alembic import context

from app.core.config import settings
from app.models.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_async_url() -> str:
    """Ensure the URL uses asyncpg driver for async migrations."""
    url = settings.DATABASE_URL
    return url.replace("postgresql://", "postgresql+asyncpg://") \
        .replace("postgres://", "postgresql+asyncpg://")


def get_sync_url() -> str:
    """Use psycopg2 for offline mode (sync)."""
    url = settings.DATABASE_URL
    return url.replace("postgresql+asyncpg://", "postgresql://") \
        .replace("postgres://", "postgresql://")


# Set database URL from settings
config.set_main_option("sqlalchemy.url", get_sync_url())


def run_migrations_offline() -> None:
    """Run migrations in offline mode.

    Configures the context with just a URL and not an Engine.
    Calls to context.execute() emit the given string to the script output.
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


def run_migrations_online() -> None:
    """Run migrations in online mode.

    Creates an async engine and associates a connection with the context.
    Uses asyncpg driver to support SQLAlchemy async operations.
    """
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine

    async def run_async_migrations():
        # Use async URL to ensure compatibility with asyncpg driver
        engine = create_async_engine(
            get_async_url(),
            echo=False,
        )
        async with engine.connect() as connection:
            await connection.run_sync(do_run_migrations)
        await engine.dispose()

    def do_run_migrations(connection):
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
