# System architecture

## Architectural stance

The first release uses a modular monolith API plus independently scalable workers. This keeps domain contracts, security, and database transactions coherent while preserving clear seams for later service extraction. The processing path is asynchronous because OCR, model inference, and retrieval have materially different latency and resource profiles.

## Logical components

```text
React/TypeScript client
          |
      API boundary  ---- JWT/RBAC ---- Audit writer
          |
   Case + document modules
          |
    PostgreSQL + outbox  ---- Redis queue/stream
          |                              |
   Object storage                  Processing workers
          |              /-----------+-----------+-----------\
      originals     preprocess   OCR/classify   extract   validate/fraud
                                                        |
                                              review + decision workflow
                                                        |
                                         pgvector/search + cited Q&A
```

## Module boundaries

- `identity`: users, roles, permissions, tenant context, JWT validation.
- `cases`: onboarding/loan case lifecycle and customer-safe projections.
- `documents`: metadata, versions, storage references, checksums, access checks.
- `processing`: job orchestration, stage state, retries, idempotency, dead letters.
- `extraction`: OCR/classification/entity extraction ports and evidence mapping.
- `validation`: deterministic rules, cross-document checks, policy versioning.
- `risk`: fraud features, model scoring, reason codes, human-review thresholds.
- `retrieval`: approved chunks, embeddings, tenant-scoped retrieval, citations.
- `review`: task queue, analyst actions, optimistic concurrency, decision record.
- `audit`: append-only events and access logs.

## Data flow

1. API authenticates the actor and creates a case/document version transaction.
2. The original is written to object storage using a generated key; the database stores only the key and checksum.
3. An outbox event publishes `document.uploaded` after the transaction commits.
4. A worker claims the event, creates a processing run, and executes versioned stages.
5. Each stage writes outputs and an event atomically, then schedules the next stage.
6. Low confidence, mismatch, or policy exceptions create a review task.
7. Approved content is chunked and indexed; the Q&A path applies tenant/document permissions before retrieval.
8. All state changes and protected-data reads emit audit events.

## Reliability patterns

- Outbox/inbox tables for durable event publication and consumer deduplication.
- Per-stage idempotency key: `(document_version_id, stage_name, pipeline_version)`.
- Exponential retry with bounded attempts; poison jobs move to a dead-letter queue.
- Optimistic locking on case, document, review task, and decision records.
- Timeouts and circuit breakers around OCR, LLM, storage, and embedding providers.
- Human review is a safe terminal state for uncertainty; automated stages do not bypass it.

## Security boundaries

- Tenant context is derived from the authenticated token, never from a client-supplied filter alone.
- Repository methods require tenant scope; cross-tenant queries are rejected by default.
- Raw document bytes are accessible only to authorized processing/review paths.
- UI receives masked values by default and requests narrowly scoped reveal permissions.
- Prompt construction strips secrets and includes only permitted document spans.
- Audit records contain identifiers and action metadata, not document contents.

## Deployment shape

Initial deployment:

- API container: FastAPI/Uvicorn.
- Worker containers: separate OCR, ML, and workflow worker pools sharing the same code contracts.
- PostgreSQL with JSONB plus `pgvector` when retrieval is introduced.
- Redis for queue/short-lived state; S3-compatible object storage for originals and page artifacts.
- Reverse proxy/API gateway, centralized logs, metrics, traces, and secret manager.

The first split candidates are OCR/ML workers and retrieval if their CPU/GPU or scaling profile diverges. The API and domain modules should remain together until transaction and ownership boundaries are proven by load and team constraints.
