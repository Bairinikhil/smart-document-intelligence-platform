# Low-level design

## Core identifiers and state

All primary identifiers are UUIDs. Every business table carries `tenant_id`, `created_at`, `updated_at`, and an optimistic-lock version where concurrent editing is possible.

Document lifecycle:

```text
UPLOADED -> PROCESSING -> NEEDS_REVIEW -> APPROVED
                         |             \-> REJECTED
                         \-> FAILED -> PROCESSING (retry)
```

Only the workflow service may perform transitions. API handlers validate commands; they do not mutate status directly.

## Relational model

- `tenants(id, name, status)`
- `users(id, tenant_id, subject, status)`
- `roles(id, tenant_id, name)`
- `user_roles(user_id, role_id)`
- `cases(id, tenant_id, external_ref, case_type, status, version)`
- `documents(id, tenant_id, case_id, document_type, status, version)`
- `document_versions(id, document_id, object_key, sha256, mime_type, size_bytes, page_count, status)`
- `processing_runs(id, document_version_id, pipeline_version, status, started_at, completed_at)`
- `processing_stage_runs(id, processing_run_id, stage, status, idempotency_key, error_code, metrics_json)`
- `extracted_fields(id, document_version_id, field_name, value_ciphertext, value_hash, confidence, evidence_json, model_version, review_state)`
- `validation_results(id, case_id, rule_code, outcome, evidence_json, policy_version)`
- `risk_scores(id, case_id, model_version, score, reason_codes_json, feature_snapshot_ref)`
- `review_tasks(id, case_id, document_version_id, task_type, status, assignee_id, priority, version)`
- `decisions(id, case_id, outcome, reason_code, actor_id, policy_version, evidence_refs_json)`
- `outbox_events(id, tenant_id, aggregate_type, aggregate_id, event_type, payload_json, published_at)`
- `audit_events(id, tenant_id, actor_id, action, resource_type, resource_id, metadata_json, occurred_at)`

Identity uses a tenant-scoped `users` table keyed by the external identity-provider
subject, a tenant-scoped `roles` table, and a `user_roles` join table. JWTs carry the
user, tenant, and role claims; the API derives permissions from server-side role
maps and never trusts client-supplied permission claims. A request's tenant scope is
always taken from the verified token context.

Sensitive extracted values should be encrypted; deterministic lookups use a keyed hash in `value_hash`. Full Aadhaar should not be required by default; store the minimum permitted representation and a masked display value.

## API surface

### Health

- `GET /v1/health/live` — process is running.
- `GET /v1/health/ready` — dependencies required for serving are reachable.

### Cases and documents

- `POST /v1/cases`
- `GET /v1/cases/{case_id}`
- `POST /v1/cases/{case_id}/documents` — returns upload slot/document version.
- `GET /v1/documents/{document_id}`
- `GET /v1/documents/{document_id}/processing`

### Review and decisions

- `GET /v1/review-tasks`
- `POST /v1/review-tasks/{task_id}/claim`
- `POST /v1/review-tasks/{task_id}/resolve`
- `POST /v1/cases/{case_id}/decision`

### Retrieval

- `POST /v1/cases/{case_id}/search`
- `POST /v1/cases/{case_id}/ask` — response must include citations and confidence metadata.

All mutating endpoints accept an `Idempotency-Key` and return a correlation ID. Error responses use a stable code, human-safe message, and correlation ID; they never echo document text or tokens.

Protected endpoints require a bearer token with `sub`, `tenant_id`, `iat`, `exp`, and
issuer claims. Authorization failures return 401 for missing/invalid tokens and 403
for insufficient permissions. Audit events are append-only records written in the
same transaction as the protected business action.

## Event contracts

Events use an envelope: `event_id`, `event_type`, `occurred_at`, `tenant_id`, `aggregate_id`, `schema_version`, and `payload`.

Initial events:

- `document.uploaded`
- `document.processing_started`
- `document.stage_completed`
- `document.review_required`
- `review_task.resolved`
- `case.decision_recorded`

Consumers must tolerate duplicate delivery and unknown additive fields.

## Testing strategy

- Unit: state transitions, validators, masking, policy predicates, retry classification.
- Contract: API schemas and event envelopes.
- Integration: PostgreSQL migrations, outbox publisher, object storage, queue, and RBAC filters.
- Workflow: synthetic documents for each supported type, including low-quality and mismatch cases.
- Security: tenant isolation, authorization matrix, prompt/data leakage checks, secret scanning.
- Performance: upload acknowledgement, worker throughput, OCR queue saturation, retrieval latency.

No test fixture may contain real identity or financial data.
