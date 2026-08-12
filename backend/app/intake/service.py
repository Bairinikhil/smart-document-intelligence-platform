from collections.abc import Mapping
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Case, Document, DocumentStatus, DocumentVersion, IdempotencyRecord
from app.intake.idempotency import find_replay, request_hash
from app.intake.schemas import CreateCaseRequest, CreateDocumentRequest
from app.security.audit import record_audit_event
from app.security.auth import Principal
from app.storage.ports import ObjectStorage, document_object_key


def _require_idempotency_key(key: str | None) -> str:
    if key is None or not key.strip() or len(key) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header is required and must be at most 100 characters",
        )
    return key.strip()


async def _save_idempotency_record(
    session: AsyncSession,
    *,
    principal: Principal,
    key: str,
    payload: Mapping[str, Any],
    response: dict[str, Any],
    resource_type: str,
    resource_id: UUID,
) -> None:
    session.add(
        IdempotencyRecord(
            tenant_id=principal.tenant_id,
            key=key,
            request_hash=request_hash(payload),
            response_json=response,
            resource_type=resource_type,
            resource_id=resource_id,
        )
    )


async def create_case(
    session: AsyncSession,
    *,
    principal: Principal,
    request: CreateCaseRequest,
    idempotency_key: str | None,
) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    payload = request.model_dump(mode="json")
    try:
        replay = await find_replay(
            session,
            tenant_id=principal.tenant_id,
            key=key,
            payload_hash=request_hash(payload),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if replay is not None:
        return replay

    case = Case(
        tenant_id=principal.tenant_id,
        case_type=request.case_type,
        external_ref=request.external_ref,
    )
    session.add(case)
    await session.flush()
    response = {
        "id": str(case.id),
        "tenant_id": str(case.tenant_id),
        "case_type": case.case_type,
        "status": case.status,
        "external_ref": case.external_ref,
    }
    await _save_idempotency_record(
        session,
        principal=principal,
        key=key,
        payload=payload,
        response=response,
        resource_type="case",
        resource_id=case.id,
    )
    await record_audit_event(
        session,
        principal=principal,
        action="case.created",
        resource_type="case",
        resource_id=case.id,
        metadata={"case_type": request.case_type},
    )
    await session.commit()
    return response


async def create_document_upload(
    session: AsyncSession,
    *,
    principal: Principal,
    case_id: UUID,
    request: CreateDocumentRequest,
    idempotency_key: str | None,
    storage: ObjectStorage,
) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    payload = request.model_dump(mode="json")
    try:
        replay = await find_replay(
            session,
            tenant_id=principal.tenant_id,
            key=key,
            payload_hash=request_hash({"case_id": str(case_id), **payload}),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if replay is not None:
        return replay

    case = await session.scalar(
        select(Case).where(Case.id == case_id, Case.tenant_id == principal.tenant_id)
    )
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="case not found")
    existing = await session.scalar(
        select(DocumentVersion).where(
            DocumentVersion.tenant_id == principal.tenant_id,
            DocumentVersion.sha256 == request.sha256,
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "document content already exists",
                "document_version_id": str(existing.id),
            },
        )

    document = Document(
        tenant_id=principal.tenant_id,
        case_id=case.id,
        document_type=request.document_type,
        status=DocumentStatus.UPLOADED,
    )
    session.add(document)
    await session.flush()
    document_version = DocumentVersion(
        tenant_id=principal.tenant_id,
        document_id=document.id,
        object_key="pending",
        sha256=request.sha256,
        mime_type=request.mime_type,
        size_bytes=request.size_bytes,
        status=DocumentStatus.UPLOADED,
    )
    session.add(document_version)
    await session.flush()
    object_key = document_object_key(
        tenant_id=principal.tenant_id,
        case_id=case.id,
        document_id=document.id,
        version_id=document_version.id,
    )
    document_version.object_key = object_key
    slot = await storage.create_upload_slot(
        tenant_id=principal.tenant_id,
        object_key=object_key,
        content_type=request.mime_type,
        content_length=request.size_bytes,
    )
    response = {
        "document_id": str(document.id),
        "document_version_id": str(document_version.id),
        "case_id": str(case.id),
        "document_type": document.document_type,
        "status": document.status,
        "object_key": slot.object_key,
        "upload_url": slot.upload_url,
        "upload_url_expires_at": slot.expires_at.isoformat(),
    }
    await _save_idempotency_record(
        session,
        principal=principal,
        key=key,
        payload={"case_id": str(case_id), **payload},
        response=response,
        resource_type="document_version",
        resource_id=document_version.id,
    )
    await record_audit_event(
        session,
        principal=principal,
        action="document.upload_slot_created",
        resource_type="document_version",
        resource_id=document_version.id,
        metadata={"document_type": request.document_type, "size_bytes": request.size_bytes},
    )
    await session.commit()
    return response
