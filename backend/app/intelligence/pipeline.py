from dataclasses import dataclass

from app.intelligence.classification import KeywordDocumentClassifier
from app.intelligence.contracts import Classification, OcrPage
from app.intelligence.ocr import TextFixtureOcr
from app.intelligence.preprocessing import BasicDocumentPreprocessor


@dataclass(frozen=True)
class IntelligenceResult:
    pages: tuple[OcrPage, ...]
    classification: Classification


class BaselineIntelligencePipeline:
    """Compose the provider ports into a deterministic local pipeline."""

    def __init__(self) -> None:
        self.preprocessor = BasicDocumentPreprocessor()
        self.ocr = TextFixtureOcr()
        self.classifier = KeywordDocumentClassifier()

    async def run(self, content: bytes, mime_type: str) -> IntelligenceResult:
        page_artifacts = self.preprocessor.preprocess(content, mime_type)
        pages = await self.ocr.recognize(page_artifacts)
        return IntelligenceResult(pages=pages, classification=self.classifier.classify(pages))
