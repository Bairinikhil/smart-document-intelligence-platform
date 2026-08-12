from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class PageArtifact:
    page_number: int
    content: bytes
    width: int | None = None
    height: int | None = None
    rotation: int = 0
    quality_score: float | None = None


@dataclass(frozen=True)
class OcrBlock:
    text: str
    confidence: float
    page_number: int
    bounding_box: tuple[float, float, float, float] | None = None


@dataclass(frozen=True)
class OcrPage:
    page_number: int
    text: str
    confidence: float
    blocks: tuple[OcrBlock, ...]
    provider: str
    model_version: str


@dataclass(frozen=True)
class Classification:
    label: str
    confidence: float
    alternatives: tuple[tuple[str, float], ...]
    model_version: str


class DocumentPreprocessor(Protocol):
    def preprocess(self, content: bytes, mime_type: str) -> tuple[PageArtifact, ...]: ...


class OcrProvider(Protocol):
    async def recognize(self, pages: tuple[PageArtifact, ...]) -> tuple[OcrPage, ...]: ...


class DocumentClassifier(Protocol):
    def classify(self, pages: tuple[OcrPage, ...]) -> Classification: ...
