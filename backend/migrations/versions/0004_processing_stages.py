"""Add durable processing stage runs for asynchronous document workflows."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0004_processing_stages"
down_revision: Union[str, None] = "0003_intake_idempotency"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    uuid = sa.Uuid()
    timestamp = sa.DateTime(timezone=True)
    op.create_table(
        "processing_stage_runs",
        sa.Column("id", uuid, nullable=False),
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("processing_run_id", uuid, nullable=False),
        sa.Column("stage", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("idempotency_key", sa.String(length=160), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("started_at", timestamp, nullable=True),
        sa.Column("completed_at", timestamp, nullable=True),
        sa.Column("created_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["processing_run_id"], ["processing_runs.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_processing_stage_runs_run_stage",
        "processing_stage_runs",
        ["processing_run_id", "stage", "idempotency_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_processing_stage_runs_run_stage", table_name="processing_stage_runs")
    op.drop_table("processing_stage_runs")
