"""Add tenant-scoped idempotency records for intake commands."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0003_intake_idempotency"
down_revision: Union[str, None] = "0002_identity_audit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    uuid = sa.Uuid()
    timestamp = sa.DateTime(timezone=True)
    op.create_table(
        "idempotency_records",
        sa.Column("id", uuid, nullable=False),
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("response_json", sa.JSON(), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=False),
        sa.Column("resource_id", uuid, nullable=False),
        sa.Column("created_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_idempotency_records_tenant_key",
        "idempotency_records",
        ["tenant_id", "key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_idempotency_records_tenant_key", table_name="idempotency_records")
    op.drop_table("idempotency_records")
