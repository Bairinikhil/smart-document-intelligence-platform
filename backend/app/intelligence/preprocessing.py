from app.intelligence.contracts import PageArtifact


class UnsupportedDocumentError(ValueError):
    """Raised when preprocessing cannot safely interpret the uploaded format."""


class BasicDocumentPreprocessor:
    """Safe baseline preprocessor for text fixtures and provider handoff."""

    supported_mime_types = frozenset({"text/plain", "application/pdf", "image/png", "image/jpeg"})

    def preprocess(self, content: bytes, mime_type: str) -> tuple[PageArtifact, ...]:
        if not content:
            raise UnsupportedDocumentError("document content cannot be empty")
        if mime_type not in self.supported_mime_types:
            raise UnsupportedDocumentError(f"unsupported document type: {mime_type}")
        return (PageArtifact(page_number=1, content=content, quality_score=1.0),)
