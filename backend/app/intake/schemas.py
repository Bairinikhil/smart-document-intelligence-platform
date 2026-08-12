from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, field_validator


CaseType = Literal["onboarding", "loan"]
DocumentType = Literal["aadhaar", "pan", "bank_statement", "salary_slip", "loan_agreement"]


class CreateCaseRequest(BaseModel):
    case_type: CaseType
    external_ref: Annotated[
        str | None, StringConstraints(strip_whitespace=True, max_length=120)
    ] = None


class CreateDocumentRequest(BaseModel):
    document_type: DocumentType
    filename: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
    mime_type: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
    ]
    size_bytes: int = Field(gt=0, le=25 * 1024 * 1024)
    sha256: Annotated[str, StringConstraints(strip_whitespace=True, min_length=64, max_length=64)]

    @field_validator("sha256")
    @classmethod
    def normalize_sha256(cls, value: str) -> str:
        value = value.lower()
        if any(character not in "0123456789abcdef" for character in value):
            raise ValueError("sha256 must be a hexadecimal digest")
        return value


class CaseResponse(BaseModel):
    id: str
    tenant_id: str
    case_type: str
    status: str
    external_ref: str | None


class DocumentUploadResponse(BaseModel):
    document_id: str
    document_version_id: str
    case_id: str
    document_type: str
    status: str
    object_key: str
    upload_url: str
    upload_url_expires_at: str
