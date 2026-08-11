# Delivery roadmap

Each step is intended to be one focused branch and draft PR. Merge only after checks pass and the design notes are updated when a decision changes.

1. **Foundation** — repository hygiene, architecture baseline, domain lifecycle, health endpoint.
2. **Persistence** — settings, SQLAlchemy models, Alembic baseline, PostgreSQL health/readiness.
3. **Identity** — JWT validation, tenant context, RBAC dependency, audit primitives.
4. **Case/document intake** — upload slots, object-storage port, checksum/idempotency, document APIs.
5. **Async processing** — outbox, queue worker, processing-run state machine, retry/dead-letter handling.
6. **OCR and classification** — preprocessing interfaces, OCR adapter, document-type classifier, evidence schema.
7. **Extraction and validation** — spaCy/entity adapters, typed field persistence, rule engine, cross-document checks.
8. **Review workflow** — LangGraph-based review routing, analyst APIs, optimistic locking, decision records.
9. **Fraud signals** — feature contract, Scikit-Learn/XGBoost inference adapter, reason codes, threshold governance.
10. **RAG** — approved chunking, embeddings, pgvector retrieval, LangChain Q&A with citations and access filters.
11. **Frontend** — React/TypeScript case inbox, upload progress, review workspace, evidence/citation UI.
12. **Production hardening** — Docker Compose, CI, observability, load tests, migration checks, security review, deployment runbook.

The first release should support one complete vertical slice: upload a synthetic PAN or salary-slip fixture, process it through deterministic adapters, show extracted evidence, and route low confidence to review. Vendor integrations and model tuning follow that slice.
