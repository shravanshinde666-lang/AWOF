"""Initial durable AWOF dataset and stage persistence.

Revision ID: 20260923_01
Revises: None
"""

from alembic import op
import sqlalchemy as sa


revision = "20260923_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "datasets",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False, unique=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "dataset_stages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("dataset_id", sa.String(length=36), sa.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stage", sa.String(length=80), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("dataset_id", "stage", name="uq_dataset_stage"),
    )
    op.create_index("ix_dataset_stages_dataset_id", "dataset_stages", ["dataset_id"])
    op.create_index("ix_dataset_stages_stage", "dataset_stages", ["stage"])
    op.create_table(
        "research_experiments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("dataset_id", sa.String(length=36), sa.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_research_experiments_dataset_id", "research_experiments", ["dataset_id"])


def downgrade() -> None:
    op.drop_index("ix_research_experiments_dataset_id", table_name="research_experiments")
    op.drop_table("research_experiments")
    op.drop_index("ix_dataset_stages_stage", table_name="dataset_stages")
    op.drop_index("ix_dataset_stages_dataset_id", table_name="dataset_stages")
    op.drop_table("dataset_stages")
    op.drop_table("datasets")
