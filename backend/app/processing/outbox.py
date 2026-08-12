from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.processing.events import event_from_outbox, pending_events
from app.processing.queue import JobQueue, ProcessingJob


async def publish_pending_events(
    session: AsyncSession,
    queue: JobQueue,
    *,
    limit: int = 100,
) -> int:
    """Publish committed outbox rows and mark them only after queue acceptance."""

    events = await pending_events(session, limit=limit)
    for event in events:
        envelope = event_from_outbox(event)
        await queue.enqueue(
            ProcessingJob(
                job_id=str(uuid4()),
                event_type=envelope.event_type,
                payload=envelope.as_payload(),
            )
        )
        event.published_at = datetime.now(timezone.utc)
    if events:
        await session.commit()
    return len(events)
