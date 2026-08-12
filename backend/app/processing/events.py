from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import OutboxEvent


@dataclass(frozen=True)
class EventEnvelope:
    event_id: UUID
    event_type: str
    tenant_id: UUID
    aggregate_id: UUID
    schema_version: int
    occurred_at: datetime
    payload: dict[str, Any]

    def as_payload(self) -> dict[str, Any]:
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "tenant_id": str(self.tenant_id),
            "aggregate_id": str(self.aggregate_id),
            "schema_version": self.schema_version,
            "occurred_at": self.occurred_at.isoformat(),
            "payload": self.payload,
        }


def event_from_outbox(event: OutboxEvent) -> EventEnvelope:
    return EventEnvelope(
        event_id=event.id,
        event_type=event.event_type,
        tenant_id=event.tenant_id,
        aggregate_id=event.aggregate_id,
        schema_version=event.schema_version,
        occurred_at=event.created_at or datetime.now(timezone.utc),
        payload=event.payload,
    )


async def append_event(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    aggregate_type: str,
    aggregate_id: UUID,
    event_type: str,
    payload: dict[str, Any],
    schema_version: int = 1,
) -> OutboxEvent:
    event = OutboxEvent(
        id=uuid4(),
        tenant_id=tenant_id,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        event_type=event_type,
        schema_version=schema_version,
        payload=payload,
    )
    session.add(event)
    await session.flush()
    return event


async def pending_events(session: AsyncSession, limit: int = 100) -> list[OutboxEvent]:
    result = await session.scalars(
        select(OutboxEvent)
        .where(OutboxEvent.published_at.is_(None))
        .order_by(OutboxEvent.created_at)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    return list(result)
