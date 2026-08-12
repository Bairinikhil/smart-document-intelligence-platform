"""Add page-level OCR evidence and document classification artifacts."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0005_ocr_classification"
down_revision: Union[str, None] = "0004_processing_stages"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    uuid = sa.Uuid()
    timestamp = sa.DateTime(timezone=True)
    op.create_table(
        "document_pages",
        sa.Column("id", uuid, nullable=False),
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("document_version_id", uuid, nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("rotation", sa.Integer(), nullable=False),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("artifact_key", sa.String(length=500), nullable=True),
        sa.Column("created_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["document_version_id"], ["document_versions.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_document_pages_version_number",
        "document_pages",
        ["document_version_id", "page_number"],
        unique=True,
    )
    op.create_table(
        "ocr_page_results",
        sa.Column("id", uuid, nullable=False),
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("page_id", uuid, nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("blocks", sa.JSON(), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("model_version", sa.String(length=80), nullable=False),
        sa.Column("created_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["page_id"], ["document_pages.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("page_id"),
    )
    op.create_table(
        "document_classifications",
        sa.Column("id", uuid, nullable=False),
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("document_version_id", uuid, nullable=False),
        sa.Column("label", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("alternatives", sa.JSON(), nullable=False),
        sa.Column("model_version", sa.String(length=80), nullable=False),
        sa.Column("created_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["document_version_id"], ["document_versions.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_document_classifications_version_created",
        "document_classifications",
        ["document_version_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_document_classifications_version_created", table_name="document_classifications"
    )
    op.drop_table("document_classifications")
    op.drop_table("ocr_page_results")
    op.drop_index("ix_document_pages_version_number", table_name="document_pages")
    op.drop_table("document_pages")
