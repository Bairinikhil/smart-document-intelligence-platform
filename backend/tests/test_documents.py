from uuid import uuid4

import pytest

from app.domain.documents import Document, DocumentStatus, InvalidDocumentTransition


def test_document_can_be_sent_to_review_and_approved() -> None:
    document = Document(tenant_id=uuid4(), case_id=uuid4(), document_type="pan")

    document.transition(DocumentStatus.PROCESSING)
    document.transition(DocumentStatus.NEEDS_REVIEW)
    document.transition(DocumentStatus.APPROVED)

    assert document.status is DocumentStatus.APPROVED
    assert document.version == 3


def test_failed_processing_can_be_retried() -> None:
    document = Document(tenant_id=uuid4(), case_id=uuid4(), document_type="salary_slip")

    document.transition(DocumentStatus.PROCESSING)
    document.transition(DocumentStatus.FAILED)
    document.transition(DocumentStatus.PROCESSING)

    assert document.status is DocumentStatus.PROCESSING


def test_terminal_document_cannot_be_reopened() -> None:
    document = Document(tenant_id=uuid4(), case_id=uuid4(), document_type="aadhaar")
    document.transition(DocumentStatus.PROCESSING)
    document.transition(DocumentStatus.REJECTED)

    with pytest.raises(InvalidDocumentTransition):
        document.transition(DocumentStatus.PROCESSING)
