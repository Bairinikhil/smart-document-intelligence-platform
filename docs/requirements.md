# Requirements baseline

## Personas

- Applicant/customer: submits documents and sees progress, requests, and final status.
- Operations analyst: reviews low-confidence extraction, mismatches, and fraud signals.
- Credit/KYC officer: approves or rejects a case using evidence and policy checks.
- Platform administrator: manages users, roles, policies, document types, and retention.
- Auditor: reads immutable decision and access history without changing business data.

## Functional requirements

### Case and document intake

1. Create an onboarding or loan case with a tenant/customer reference.
2. Upload a document version with MIME type, size, checksum, and source metadata.
3. Store the original in encrypted object storage; keep metadata and derived facts in PostgreSQL.
4. Deduplicate by tenant-scoped content hash without exposing raw PII in logs.
5. Track asynchronous processing with idempotent jobs and retryable stages.

### Intelligence pipeline

1. Preprocess pages: orientation, crop, denoise, contrast, and quality scoring.
2. Run OCR with page-level text and bounding-box confidence.
3. Classify document type and detect unsupported or suspicious document formats.
4. Extract typed fields such as name, PAN, Aadhaar reference, IFSC, account number, employer, and salary.
5. Persist every extracted value with confidence, source page/region, model version, and review state.
6. Validate format, cross-document consistency, expiry, mandatory fields, and configurable business rules.
7. Generate explainable fraud signals; route only policy-approved actions automatically.
8. Index approved text/chunks for access-controlled retrieval and citation-backed Q&A.

### Review and decisions

1. Create review tasks when confidence or validation thresholds are not met.
2. Support claim, release, approve, reject, and request-correction actions with reasons.
3. Record decision evidence, actor, timestamp, model/policy versions, and before/after state.
4. Prevent a generated answer from being treated as source evidence unless it links to stored document spans.

### Security and governance

1. Authenticate with short-lived JWT access tokens and rotating refresh tokens.
2. Enforce tenant isolation and RBAC at the API/service boundary and in repository queries.
3. Mask PAN/Aadhaar/account identifiers in UI, logs, metrics, and error messages.
4. Encrypt data in transit and at rest; keep secrets outside source control.
5. Make audit events append-only and queryable by case, actor, resource, and time range.
6. Apply configurable retention, deletion, legal hold, and export workflows.

## Non-functional requirements

- Upload acknowledgement: p95 under 500 ms excluding client transfer.
- Pipeline target: p95 under 30 seconds for a normal five-page document in the initial deployment.
- Availability target: 99.9% for API and 99.5% for asynchronous processing workers.
- At-least-once job delivery with idempotent stage handlers.
- Correlation IDs across API request, job, model inference, and audit records.
- No production PII in fixtures, test snapshots, traces, or developer logs.
- Every model and policy change is versioned and observable.

## Explicit non-goals for the first release

- Direct integration with UIDAI, PAN, bank, or bureau systems.
- Fully autonomous credit approval or fraud rejection.
- Multi-region active/active deployment.
- Training models on customer data inside the application runtime.
- Supporting every possible Indian document type before the core workflow is reliable.

## Open decisions to confirm before production

- Approved OCR/LLM vendors and Indian-region hosting requirements.
- Retention periods and deletion/legal-hold policy with the compliance owner.
- Exact KYC/AML/DPDP obligations for the client deployment.
- Human-review SLA, approval quorum, and escalation policy.
- Target throughput, maximum file/page sizes, and tenant count.
