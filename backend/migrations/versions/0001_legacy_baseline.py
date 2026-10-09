from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0001_legacy_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    existing_tables = set(inspect(bind).get_table_names())

    if "complaints" not in existing_tables:
        op.create_table(
            "complaints",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("complaint_id", sa.String(length=32), nullable=False),
            sa.Column("text", sa.Text(), nullable=False),
            sa.Column("latitude", sa.Float(), nullable=False),
            sa.Column("longitude", sa.Float(), nullable=False),
            sa.Column("image_path", sa.String(length=255), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("is_flagged", sa.Boolean(), nullable=False),
            sa.Column("flag_reason", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_complaints_id", "complaints", ["id"])
        op.create_index(
            "ix_complaints_complaint_id",
            "complaints",
            ["complaint_id"],
            unique=True,
        )

    existing_tables = set(inspect(bind).get_table_names())
    if "complaint_preprocessing" not in existing_tables:
        op.create_table(
            "complaint_preprocessing",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("complaint_id", sa.Integer(), nullable=False),
            sa.Column("pipeline_version", sa.String(length=32), nullable=False),
            sa.Column("language_model", sa.String(length=64), nullable=False),
            sa.Column("normalization_model", sa.String(length=64), nullable=False),
            sa.Column("is_current", sa.Boolean(), nullable=False),
            sa.Column("detected_language", sa.String(length=16), nullable=False),
            sa.Column("detected_script", sa.String(length=16), nullable=False),
            sa.Column("language_confidence", sa.Float(), nullable=False),
            sa.Column("is_code_mixed", sa.Boolean(), nullable=False),
            sa.Column("original_text", sa.Text(), nullable=False),
            sa.Column("normalized_text", sa.Text(), nullable=False),
            sa.Column("translation_en", sa.Text(), nullable=True),
            sa.Column("processing_method", sa.String(length=32), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(
                ["complaint_id"], ["complaints.id"], ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_complaint_preprocessing_id", "complaint_preprocessing", ["id"])
        op.create_index(
            "ix_complaint_preprocessing_complaint_id",
            "complaint_preprocessing",
            ["complaint_id"],
        )
        op.create_index(
            "ix_complaint_preprocessing_is_current",
            "complaint_preprocessing",
            ["is_current"],
        )


def downgrade() -> None:
    pass