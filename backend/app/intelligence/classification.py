from collections import Counter

from app.intelligence.contracts import Classification, DocumentClassifier, OcrPage


class KeywordDocumentClassifier:
    """Explainable baseline classifier for synthetic fixtures and smoke tests."""

    model_version = "keyword-v1"
    _signals: dict[str, frozenset[str]] = {
        "pan": frozenset({"income tax", "permanent account number", "pan"}),
        "aadhaar": frozenset({"aadhaar", "uidai", "unique identification"}),
        "bank_statement": frozenset(
            {"bank statement", "ifsc", "opening balance", "closing balance"}
        ),
        "salary_slip": frozenset({"salary", "gross pay", "net pay", "pay slip", "payslip"}),
        "loan_agreement": frozenset({"loan agreement", "borrower", "sanction", "repayment"}),
    }

    def classify(self, pages: tuple[OcrPage, ...]) -> Classification:
        text = " ".join(page.text.lower() for page in pages)
        scores = Counter(
            {
                label: sum(1 for signal in signals if signal in text)
                for label, signals in self._signals.items()
            }
        )
        ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
        winning_label, winning_score = ranked[0]
        total_signals = sum(scores.values())
        confidence = winning_score / total_signals if total_signals else 0.0
        alternatives = tuple(
            (label, count / total_signals if total_signals else 0.0)
            for label, count in ranked[1:3]
            if count
        )
        return Classification(
            label=winning_label if winning_score else "unknown",
            confidence=confidence,
            alternatives=alternatives,
            model_version=self.model_version,
        )


def ensure_classifier(classifier: object) -> DocumentClassifier:
    if not hasattr(classifier, "classify"):
        raise TypeError("classifier must implement classify(pages)")
    return classifier  # type: ignore[return-value]
