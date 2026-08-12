from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable

from app.intelligence.extraction import FieldEvidence


class ValidationOutcome(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    REVIEW = "review"


@dataclass(frozen=True)
class ValidationResult:
    rule_code: str
    outcome: ValidationOutcome
    evidence: dict[str, object]
    policy_version: str


def validate_field_formats(
    fields: Iterable[FieldEvidence], policy_version: str = "v1"
) -> tuple[ValidationResult, ...]:
    results: list[ValidationResult] = []
    for field in fields:
        if field.field_name == "pan":
            outcome = ValidationOutcome.PASS if len(field.value) == 10 else ValidationOutcome.FAIL
            rule = "PAN_FORMAT"
        elif field.field_name == "aadhaar":
            outcome = ValidationOutcome.PASS if len(field.value) == 12 else ValidationOutcome.FAIL
            rule = "AADHAAR_FORMAT"
        elif field.field_name == "ifsc":
            outcome = ValidationOutcome.PASS if len(field.value) == 11 else ValidationOutcome.FAIL
            rule = "IFSC_FORMAT"
        else:
            outcome = (
                ValidationOutcome.PASS if field.confidence >= 0.85 else ValidationOutcome.REVIEW
            )
            rule = "FIELD_CONFIDENCE"
        results.append(
            ValidationResult(
                rule_code=rule,
                outcome=outcome,
                evidence={"field_name": field.field_name, "page_number": field.page_number},
                policy_version=policy_version,
            )
        )
    return tuple(results)


def validate_cross_document_identity(
    fields: Iterable[FieldEvidence], policy_version: str = "v1"
) -> tuple[ValidationResult, ...]:
    grouped: dict[str, set[str]] = {}
    for field in fields:
        if field.field_name in {"pan", "aadhaar"}:
            grouped.setdefault(field.field_name, set()).add(field.value)
    return tuple(
        ValidationResult(
            rule_code=f"{field_name.upper()}_CROSS_DOCUMENT_MATCH",
            outcome=ValidationOutcome.PASS if len(values) == 1 else ValidationOutcome.REVIEW,
            evidence={"field_name": field_name, "observed_values": len(values)},
            policy_version=policy_version,
        )
        for field_name, values in grouped.items()
    )
