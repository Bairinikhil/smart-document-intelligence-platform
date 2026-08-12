import asyncio

import pytest

from app.intelligence.classification import KeywordDocumentClassifier
from app.intelligence.contracts import PageArtifact
from app.intelligence.ocr import TextFixtureOcr
from app.intelligence.pipeline import BaselineIntelligencePipeline
from app.intelligence.preprocessing import BasicDocumentPreprocessor, UnsupportedDocumentError


def test_preprocessor_rejects_unknown_formats() -> None:
    with pytest.raises(UnsupportedDocumentError):
        BasicDocumentPreprocessor().preprocess(b"secret", "application/x-unknown")


def test_fixture_ocr_preserves_page_evidence() -> None:
    async def scenario() -> None:
        pages = await TextFixtureOcr().recognize(
            (PageArtifact(page_number=2, content=b"PAN ABCDE1234F"),)
        )
        assert pages[0].page_number == 2
        assert pages[0].text == "PAN ABCDE1234F"
        assert pages[0].blocks[1].text == "ABCDE1234F"
        assert pages[0].confidence == 0.99

    asyncio.run(scenario())


def test_keyword_classifier_identifies_salary_slip() -> None:
    async def scenario() -> None:
        result = await BaselineIntelligencePipeline().run(
            b"Salary Slip\nGross Pay 100000\nNet Pay 82000", "text/plain"
        )
        assert result.classification.label == "salary_slip"
        assert result.classification.confidence == 1.0

    asyncio.run(scenario())


def test_unknown_content_is_explicitly_low_confidence() -> None:
    pages = asyncio.run(TextFixtureOcr().recognize((PageArtifact(1, b"unrelated text"),)))
    result = KeywordDocumentClassifier().classify(pages)

    assert result.label == "unknown"
    assert result.confidence == 0.0
