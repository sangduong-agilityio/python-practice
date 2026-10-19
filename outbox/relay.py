import asyncio
from typing import Dict, List, Callable, Any

class OutboxRelay:
    """Dispatches persisted outbox events to external systems."""
    def __init__(self, uow_factory, event_handlers: Dict[str, List[Callable]]):
        self.uow_factory = uow_factory
        self.handlers = event_handlers

    async def drain_once(self):
        """Fetch pending events, dispatch to handlers, and mark them dispatched."""
        async with self.uow_factory() as uow:
            # 1. Fetch pending outbox records
            pending = await uow.session.execute("SELECT id, type, payload FROM outbox WHERE dispatched = FALSE FOR UPDATE")
            events = pending.fetchall()

            for event in events:
                # 2. Dispatch to external broker / handler
                await self.dispatch(event)
                # 3. Mark dispatched
                await uow.session.execute("UPDATE outbox SET dispatched = TRUE WHERE id = :id", {"id": event.id})

            # Commit the batch update
            await uow.commit()

    async def dispatch(self, event):
        """Dispatch event payload to registered handlers.
        Handlers must be idempotent: if a crash happens before commit,
        the event will be redelivered on the next drain iteration.
        """
        for handler in self.handlers.get(event.type, []):
            await handler(event.payload)
