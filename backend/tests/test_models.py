from app.db.models import Base


def test_initial_schema_contains_required_tables() -> None:
    expected = {
        "tenants",
        "cases",
        "documents",
        "document_versions",
        "processing_runs",
        "outbox_events",
    }

    assert expected.issubset(Base.metadata.tables)
