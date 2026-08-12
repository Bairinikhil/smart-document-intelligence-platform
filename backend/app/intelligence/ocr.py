import re

from app.intelligence.contracts import OcrBlock, OcrPage, OcrProvider, PageArtifact


class TextFixtureOcr:
    """Deterministic OCR double for local tests and synthetic fixtures."""

    provider = "text-fixture"
    model_version = "fixture-v1"

    async def recognize(self, pages: tuple[PageArtifact, ...]) -> tuple[OcrPage, ...]:
        results: list[OcrPage] = []
        for page in pages:
            text = page.content.decode("utf-8", errors="replace")
            blocks = tuple(
                OcrBlock(text=match.group(0), confidence=0.99, page_number=page.page_number)
                for match in re.finditer(r"\S+", text)
            )
            results.append(
                OcrPage(
                    page_number=page.page_number,
                    text=text,
                    confidence=0.99 if text.strip() else 0.0,
                    blocks=blocks,
                    provider=self.provider,
                    model_version=self.model_version,
                )
            )
        return tuple(results)


def ensure_ocr_provider(provider: object) -> OcrProvider:
    if not hasattr(provider, "recognize"):
        raise TypeError("OCR provider must implement recognize(pages)")
    return provider  # type: ignore[return-value]
