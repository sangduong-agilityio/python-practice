from contextlib import asynccontextmanager
from typing import AsyncGenerator, List, Any
from sqlalchemy.ext.asyncio import AsyncSession

class UnitOfWork:
    """Unit of Work implementation holding database session and outbox events."""
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.session: AsyncSession = None
        self.events: List[Any] = []

    async def __aenter__(self):
        self.session = self.session_factory()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.rollback()
        await self.session.close()

    async def commit(self):
        """Commit current transaction and collect pending domain events."""
        await self.session.commit()
        events_to_dispatch = list(self.events)
        self.events.clear()
        return events_to_dispatch

    async def rollback(self):
        """Rollback transaction and discard pending events."""
        await self.session.rollback()
        self.events.clear()

    def collect(self, event):
        """Buffer domain event until transaction commits successfully."""
        self.events.append(event)
