from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Uuid,
    func,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class CaseStatus(StrEnum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CLOSED = "closed"


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"


class ProcessingStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class StageStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DEAD_LETTERED = "dead_lettered"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")

    cases: Mapped[list["Case"]] = relationship(back_populates="tenant")


class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("tenant_id", "subject", name="uq_users_tenant_subject"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")


class Role(Base, TimestampMixin):
    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_roles_tenant_name"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role_id: Mapped[UUID] = mapped_column(ForeignKey("roles.id"), primary_key=True)


class Case(Base, TimestampMixin):
    __tablename__ = "cases"
    __table_args__ = (Index("ix_cases_tenant_status", "tenant_id", "status"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    external_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    case_type: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=CaseStatus.OPEN)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    tenant: Mapped[Tenant] = relationship(back_populates="cases")
    documents: Mapped[list["Document"]] = relationship(back_populates="case")


class Document(Base, TimestampMixin):
    __tablename__ = "documents"
    __table_args__ = (Index("ix_documents_case_status", "case_id", "status"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.id"), nullable=False)
    document_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=DocumentStatus.UPLOADED)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    case: Mapped[Case] = relationship(back_populates="documents")
    versions: Mapped[list["DocumentVersion"]] = relationship(back_populates="document")


class DocumentVersion(Base, TimestampMixin):
    __tablename__ = "document_versions"
    __table_args__ = (Index("ix_document_versions_sha256", "tenant_id", "sha256"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id"), nullable=False)
    object_key: Mapped[str] = mapped_column(String(500), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=DocumentStatus.UPLOADED)

    document: Mapped[Document] = relationship(back_populates="versions")
    processing_runs: Mapped[list["ProcessingRun"]] = relationship(back_populates="document_version")
    pages: Mapped[list["DocumentPage"]] = relationship(back_populates="document_version")
    classifications: Mapped[list["DocumentClassification"]] = relationship(
        back_populates="document_version"
    )


class DocumentPage(Base, TimestampMixin):
    __tablename__ = "document_pages"
    __table_args__ = (
        Index(
            "ix_document_pages_version_number", "document_version_id", "page_number", unique=True
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    document_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("document_versions.id"), nullable=False
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rotation: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quality_score: Mapped[float | None] = mapped_column(nullable=True)
    artifact_key: Mapped[str | None] = mapped_column(String(500), nullable=True)

    document_version: Mapped[DocumentVersion] = relationship(back_populates="pages")
    ocr_result: Mapped["OcrPageResult | None"] = relationship(back_populates="page", uselist=False)


class OcrPageResult(Base, TimestampMixin):
    __tablename__ = "ocr_page_results"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    page_id: Mapped[UUID] = mapped_column(
        ForeignKey("document_pages.id"), nullable=False, unique=True
    )
    text: Mapped[str] = mapped_column(String, nullable=False, default="")
    confidence: Mapped[float] = mapped_column(nullable=False, default=0.0)
    blocks: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    model_version: Mapped[str] = mapped_column(String(80), nullable=False)

    page: Mapped[DocumentPage] = relationship(back_populates="ocr_result")


class DocumentClassification(Base, TimestampMixin):
    __tablename__ = "document_classifications"
    __table_args__ = (
        Index("ix_document_classifications_version_created", "document_version_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    document_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("document_versions.id"), nullable=False
    )
    label: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    alternatives: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    model_version: Mapped[str] = mapped_column(String(80), nullable=False)

    document_version: Mapped[DocumentVersion] = relationship(back_populates="classifications")


class ExtractedField(Base, TimestampMixin):
    __tablename__ = "extracted_fields"
    __table_args__ = (
        Index("ix_extracted_fields_version_name", "document_version_id", "field_name"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    document_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("document_versions.id"), nullable=False
    )
    field_name: Mapped[str] = mapped_column(String(80), nullable=False)
    value_ciphertext: Mapped[str] = mapped_column(String, nullable=False)
    value_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    model_version: Mapped[str] = mapped_column(String(80), nullable=False)
    review_state: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")


class ValidationResult(Base, TimestampMixin):
    __tablename__ = "validation_results"
    __table_args__ = (Index("ix_validation_results_case_rule", "case_id", "rule_code"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.id"), nullable=False)
    rule_code: Mapped[str] = mapped_column(String(100), nullable=False)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    policy_version: Mapped[str] = mapped_column(String(80), nullable=False)


class ProcessingRun(Base, TimestampMixin):
    __tablename__ = "processing_runs"
    __table_args__ = (Index("ix_processing_runs_document_status", "document_version_id", "status"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    document_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("document_versions.id"), nullable=False
    )
    pipeline_version: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=ProcessingStatus.PENDING
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    document_version: Mapped[DocumentVersion] = relationship(back_populates="processing_runs")
    stage_runs: Mapped[list["ProcessingStageRun"]] = relationship(back_populates="processing_run")


class ProcessingStageRun(Base, TimestampMixin):
    __tablename__ = "processing_stage_runs"
    __table_args__ = (
        Index(
            "ix_processing_stage_runs_run_stage",
            "processing_run_id",
            "stage",
            "idempotency_key",
            unique=True,
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    processing_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("processing_runs.id"), nullable=False
    )
    stage: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=StageStatus.PENDING)
    idempotency_key: Mapped[str] = mapped_column(String(160), nullable=False)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    processing_run: Mapped[ProcessingRun] = relationship(back_populates="stage_runs")


class OutboxEvent(Base, TimestampMixin):
    __tablename__ = "outbox_events"
    __table_args__ = (Index("ix_outbox_events_unpublished", "published_at", "created_at"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    aggregate_type: Mapped[str] = mapped_column(String(64), nullable=False)
    aggregate_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_events_tenant_occurred", "tenant_id", "occurred_at"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    actor_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    event_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )
    correlation_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class IdempotencyRecord(Base, TimestampMixin):
    __tablename__ = "idempotency_records"
    __table_args__ = (Index("ix_idempotency_records_tenant_key", "tenant_id", "key", unique=True),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    response_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
