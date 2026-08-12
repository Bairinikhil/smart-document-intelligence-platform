from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    DocumentStatus,
    DocumentVersion,
    ProcessingRun,
    ProcessingStageRun,
    ProcessingStatus,
    StageStatus,
)


PIPELINE_STAGES: tuple[str, ...] = ("preprocess", "ocr", "classify", "extract", "validate")


def stage_idempotency_key(
    document_version_id: UUID | str, stage: str, pipeline_version: str
) -> str:
    return f"{document_version_id}:{stage}:{pipeline_version}"


async def start_processing_run(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    document_version_id: UUID,
    pipeline_version: str,
) -> ProcessingRun:
    document_version = await session.scalar(
        select(DocumentVersion).where(
            DocumentVersion.id == document_version_id,
            DocumentVersion.tenant_id == tenant_id,
        )
    )
    if document_version is None:
        raise ValueError("document version is not in tenant scope")
    run = ProcessingRun(
        tenant_id=tenant_id,
        document_version_id=document_version_id,
        pipeline_version=pipeline_version,
        status=ProcessingStatus.RUNNING,
        started_at=datetime.now(timezone.utc),
    )
    document_version.status = DocumentStatus.PROCESSING
    session.add(run)
    await session.flush()
    session.add(
        ProcessingStageRun(
            tenant_id=tenant_id,
            processing_run_id=run.id,
            stage=PIPELINE_STAGES[0],
            status=StageStatus.PENDING,
            idempotency_key=stage_idempotency_key(
                document_version_id, PIPELINE_STAGES[0], pipeline_version
            ),
        )
    )
    await session.commit()
    return run
