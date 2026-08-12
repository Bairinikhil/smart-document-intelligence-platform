from app.db.models import Base


def test_initial_schema_contains_required_tables() -> None:
    expected = {
        "tenants",
        "cases",
        "documents",
        "document_versions",
        "processing_runs",
        "outbox_events",
        "users",
        "roles",
        "user_roles",
        "audit_events",
        "idempotency_records",
        "processing_stage_runs",
        "document_pages",
        "ocr_page_results",
        "document_classifications",
    }

    assert expected.issubset(Base.metadata.tables)
