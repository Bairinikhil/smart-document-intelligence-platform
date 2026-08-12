from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.intake.idempotency import request_hash
from app.intake.schemas import CreateDocumentRequest
from app.storage.ports import document_object_key


def test_document_request_normalizes_sha256() -> None:
    request = CreateDocumentRequest(
        document_type="pan",
        filename="pan.pdf",
        mime_type="application/pdf",
        size_bytes=1024,
        sha256="A" * 64,
    )

    assert request.sha256 == "a" * 64


def test_document_request_rejects_non_hex_digest() -> None:
    with pytest.raises(ValidationError):
        CreateDocumentRequest(
            document_type="pan",
            filename="pan.pdf",
            mime_type="application/pdf",
            size_bytes=1024,
            sha256="z" * 64,
        )


def test_request_hash_is_order_independent() -> None:
    assert request_hash({"b": 2, "a": 1}) == request_hash({"a": 1, "b": 2})
    assert request_hash({"a": 1}) != request_hash({"a": 2})


def test_object_key_contains_only_server_generated_identifiers() -> None:
    tenant_id, case_id, document_id, version_id = (uuid4() for _ in range(4))

    key = document_object_key(
        tenant_id=tenant_id,
        case_id=case_id,
        document_id=document_id,
        version_id=version_id,
    )

    assert key == (
        f"tenants/{tenant_id}/cases/{case_id}/documents/{document_id}/versions/{version_id}"
    )
    assert ".." not in key
