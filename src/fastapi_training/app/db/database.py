from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

# Database configuration logic for async sqlite
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./sql_app.db"

# Create async engine
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create async session local class
AsyncSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

# Base class for models
Base = declarative_base()

async def create_db_and_tables():
    from ..models import user  
    from ..models import task
    from ..models import project
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
