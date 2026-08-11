"""Document lifecycle rules.

This module intentionally has no web, database, OCR, or model dependencies. It is the
stable contract that later adapters and workflow code must respect.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID, uuid4


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"


class InvalidDocumentTransition(ValueError):
    """Raised when a document command violates the lifecycle contract."""


_ALLOWED_TRANSITIONS: dict[DocumentStatus, frozenset[DocumentStatus]] = {
    DocumentStatus.UPLOADED: frozenset({DocumentStatus.PROCESSING}),
    DocumentStatus.PROCESSING: frozenset(
        {
            DocumentStatus.NEEDS_REVIEW,
            DocumentStatus.APPROVED,
            DocumentStatus.REJECTED,
            DocumentStatus.FAILED,
        }
    ),
    DocumentStatus.NEEDS_REVIEW: frozenset(
        {DocumentStatus.PROCESSING, DocumentStatus.APPROVED, DocumentStatus.REJECTED}
    ),
    DocumentStatus.FAILED: frozenset({DocumentStatus.PROCESSING}),
    DocumentStatus.APPROVED: frozenset(),
    DocumentStatus.REJECTED: frozenset(),
}


@dataclass
class Document:
    """A document aggregate with guarded state transitions."""

    tenant_id: UUID
    case_id: UUID
    document_type: str
    id: UUID = field(default_factory=uuid4)
    status: DocumentStatus = DocumentStatus.UPLOADED
    version: int = 0
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def transition(self, target: DocumentStatus) -> None:
        if target not in _ALLOWED_TRANSITIONS[self.status]:
            raise InvalidDocumentTransition(
                f"cannot transition document from {self.status} to {target}"
            )
        self.status = target
        self.version += 1
        self.updated_at = datetime.now(timezone.utc)
