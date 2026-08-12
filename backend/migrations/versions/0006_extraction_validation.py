"""Add encrypted extraction values and case validation results."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0006_extraction_validation"
down_revision: Union[str, None] = "0005_ocr_classification"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    uuid = sa.Uuid()
    timestamp = sa.DateTime(timezone=True)
    op.create_table(
        "extracted_fields",
        sa.Column("id", uuid, nullable=False),
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("document_version_id", uuid, nullable=False),
        sa.Column("field_name", sa.String(length=80), nullable=False),
        sa.Column("value_ciphertext", sa.Text(), nullable=False),
        sa.Column("value_hash", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("model_version", sa.String(length=80), nullable=False),
        sa.Column("review_state", sa.String(length=32), nullable=False),
        sa.Column("created_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["document_version_id"], ["document_versions.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_extracted_fields_version_name",
        "extracted_fields",
        ["document_version_id", "field_name"],
    )
    op.create_table(
        "validation_results",
        sa.Column("id", uuid, nullable=False),
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("case_id", uuid, nullable=False),
        sa.Column("rule_code", sa.String(length=100), nullable=False),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("policy_version", sa.String(length=80), nullable=False),
        sa.Column("created_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_validation_results_case_rule", "validation_results", ["case_id", "rule_code"]
    )


def downgrade() -> None:
    op.drop_index("ix_validation_results_case_rule", table_name="validation_results")
    op.drop_table("validation_results")
    op.drop_index("ix_extracted_fields_version_name", table_name="extracted_fields")
    op.drop_table("extracted_fields")
