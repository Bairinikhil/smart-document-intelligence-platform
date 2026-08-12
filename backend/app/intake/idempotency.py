import hashlib
import json
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import IdempotencyRecord


def request_hash(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


async def find_replay(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    key: str,
    payload_hash: str,
) -> dict[str, Any] | None:
    record = await session.scalar(
        select(IdempotencyRecord).where(
            IdempotencyRecord.tenant_id == tenant_id,
            IdempotencyRecord.key == key,
        )
    )
    if record is None:
        return None
    if record.request_hash != payload_hash:
        raise ValueError("idempotency key was already used with a different request")
    return record.response_json
