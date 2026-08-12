from collections.abc import Mapping
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditEvent
from app.security.auth import Principal


async def record_audit_event(
    session: AsyncSession,
    *,
    principal: Principal | None,
    action: str,
    resource_type: str,
    resource_id: UUID | None = None,
    metadata: Mapping[str, str | int | bool | None] | None = None,
    correlation_id: str | None = None,
) -> AuditEvent:
    """Stage an append-only audit event in the caller's transaction."""

    if principal is None:
        raise ValueError("an authenticated principal is required for audit events")
    event = AuditEvent(
        tenant_id=principal.tenant_id,
        actor_id=principal.user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        event_metadata=dict(metadata or {}),
        correlation_id=correlation_id,
    )
    session.add(event)
    await session.flush()
    return event
