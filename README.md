# Smart Document Intelligence Platform

An Indian BFSI document-processing platform for KYC verification, loan-document analysis, and customer onboarding.

## Current status

This repository starts with the architecture and domain foundation. The first implementation slice establishes the document lifecycle contract and a health-check API. External OCR, LLM, storage, and model providers will be added behind ports with deterministic test doubles.

## Product scope

- Upload and track Aadhaar, PAN, bank statements, salary slips, and loan documents.
- Extract structured fields with OCR and NLP while preserving source evidence.
- Validate document consistency and route uncertain cases to human review.
- Expose controlled document search and question answering with citations.
- Produce auditable fraud signals and onboarding decisions without making opaque automated decisions.

## Repository layout

```text
backend/     FastAPI application and domain logic
frontend/    React + TypeScript application (introduced in a later slice)
docs/        requirements, architecture, low-level design, and delivery roadmap
```

## Local development

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

The first slice can be validated without external services:

```powershell
cd backend
python -m pytest
python -m compileall app tests
```

For persistence development, copy `backend/.env.example` to `backend/.env`, set
`SDI_DATABASE_URL`, install the data extra, and run `alembic upgrade head` from
the `backend` directory.

See [docs/roadmap.md](docs/roadmap.md) for the PR-by-PR execution plan.
