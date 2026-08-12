import hashlib
import hmac
import re
from dataclasses import dataclass
from typing import Protocol

from app.intelligence.contracts import OcrPage


@dataclass(frozen=True)
class FieldEvidence:
    field_name: str
    value: str
    confidence: float
    page_number: int
    text_span: str
    model_version: str


class ValueProtector(Protocol):
    def encrypt(self, value: str) -> str: ...

    def hash(self, value: str) -> str: ...


class DeterministicValueProtector:
    """Test-safe protector; production wiring must use a KMS-backed encryptor."""

    def __init__(self, key: bytes) -> None:
        if not key:
            raise ValueError("value protection key cannot be empty")
        self.key = key

    def encrypt(self, value: str) -> str:
        # Explicit placeholder, not production encryption.
        return value.encode("utf-8").hex()

    def hash(self, value: str) -> str:
        return hmac.new(self.key, value.encode("utf-8"), hashlib.sha256).hexdigest()


class RegexEntityExtractor:
    model_version = "regex-v1"
    _patterns: dict[str, re.Pattern[str]] = {
        "pan": re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"),
        "aadhaar": re.compile(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b"),
        "ifsc": re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b"),
        "account_number": re.compile(r"\b\d{9,18}\b"),
    }

    def extract(self, pages: tuple[OcrPage, ...]) -> tuple[FieldEvidence, ...]:
        results: list[FieldEvidence] = []
        for page in pages:
            for field_name, pattern in self._patterns.items():
                for match in pattern.finditer(page.text):
                    value = re.sub(r"[ -]", "", match.group(0))
                    results.append(
                        FieldEvidence(
                            field_name=field_name,
                            value=value,
                            confidence=min(page.confidence, 0.99),
                            page_number=page.page_number,
                            text_span=match.group(0),
                            model_version=self.model_version,
                        )
                    )
        return tuple(results)
