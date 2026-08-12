import asyncio

from app.intelligence.contracts import PageArtifact
from app.intelligence.extraction import DeterministicValueProtector, RegexEntityExtractor
from app.intelligence.ocr import TextFixtureOcr
from app.intelligence.validation import (
    ValidationOutcome,
    validate_cross_document_identity,
    validate_field_formats,
)


def _fields(text: bytes):
    pages = asyncio.run(TextFixtureOcr().recognize((PageArtifact(1, text),)))
    return RegexEntityExtractor().extract(pages)


def test_extracts_supported_indian_financial_identifiers() -> None:
    fields = _fields(b"PAN ABCDE1234F IFSC HDFC0123456 Aadhaar 1234-5678-9012")

    assert {(field.field_name, field.value) for field in fields} == {
        ("pan", "ABCDE1234F"),
        ("ifsc", "HDFC0123456"),
        ("aadhaar", "123456789012"),
    }


def test_protector_hash_is_keyed_and_ciphertext_is_separate() -> None:
    protector = DeterministicValueProtector(b"test-key")

    assert protector.encrypt("ABCDE1234F") != "ABCDE1234F"
    assert protector.hash("ABCDE1234F") == protector.hash("ABCDE1234F")
    assert protector.hash("ABCDE1234F") != DeterministicValueProtector(b"other").hash("ABCDE1234F")


def test_format_validation_passes_valid_pan_and_ifsc() -> None:
    results = validate_field_formats(_fields(b"PAN ABCDE1234F IFSC HDFC0123456"))

    assert {result.outcome for result in results} == {ValidationOutcome.PASS}


def test_cross_document_mismatch_routes_to_review() -> None:
    fields = _fields(b"PAN ABCDE1234F") + _fields(b"PAN XYZAB9876C")

    results = validate_cross_document_identity(fields)

    assert results[0].rule_code == "PAN_CROSS_DOCUMENT_MATCH"
    assert results[0].outcome is ValidationOutcome.REVIEW
