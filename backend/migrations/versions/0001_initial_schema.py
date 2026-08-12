"""Create the initial tenant, case, document, processing, and outbox tables."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    uuid = sa.Uuid()
    timestamp = sa.DateTime(timezone=True)

    op.create_table(
        "tenants",
        sa.Column("id", uuid, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "cases",
        sa.Column("id", uuid, nullable=False),
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("external_ref", sa.String(length=120), nullable=True),
        sa.Column("case_type", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cases_tenant_status", "cases", ["tenant_id", "status"])
    op.create_table(
        "documents",
        sa.Column("id", uuid, nullable=False),
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("case_id", uuid, nullable=False),
        sa.Column("document_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_documents_case_status", "documents", ["case_id", "status"])
    op.create_table(
        "document_versions",
        sa.Column("id", uuid, nullable=False),
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("document_id", uuid, nullable=False),
        sa.Column("object_key", sa.String(length=500), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_document_versions_sha256", "document_versions", ["tenant_id", "sha256"])
    op.create_table(
        "processing_runs",
        sa.Column("id", uuid, nullable=False),
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("document_version_id", uuid, nullable=False),
        sa.Column("pipeline_version", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", timestamp, nullable=True),
        sa.Column("completed_at", timestamp, nullable=True),
        sa.Column("created_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["document_version_id"], ["document_versions.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_processing_runs_document_status",
        "processing_runs",
        ["document_version_id", "status"],
    )
    op.create_table(
        "outbox_events",
        sa.Column("id", uuid, nullable=False),
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("aggregate_type", sa.String(length=64), nullable=False),
        sa.Column("aggregate_id", uuid, nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("published_at", timestamp, nullable=True),
        sa.Column("created_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_outbox_events_unpublished", "outbox_events", ["published_at", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_outbox_events_unpublished", table_name="outbox_events")
    op.drop_table("outbox_events")
    op.drop_index("ix_processing_runs_document_status", table_name="processing_runs")
    op.drop_table("processing_runs")
    op.drop_index("ix_document_versions_sha256", table_name="document_versions")
    op.drop_table("document_versions")
    op.drop_index("ix_documents_case_status", table_name="documents")
    op.drop_table("documents")
    op.drop_index("ix_cases_tenant_status", table_name="cases")
    op.drop_table("cases")
    op.drop_table("tenants")
