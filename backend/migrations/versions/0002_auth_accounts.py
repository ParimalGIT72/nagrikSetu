from alembic import op
import sqlalchemy as sa

revision = "0002_auth_accounts"
down_revision = "0001_legacy_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("token_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "role IN ('citizen', 'officer', 'admin')", name="ck_users_role"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.add_column("complaints", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_index("ix_complaints_user_id", "complaints", ["user_id"])
    op.create_foreign_key(
        "fk_complaints_user_id_users",
        "complaints",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_complaints_user_id_users", "complaints", type_="foreignkey")
    op.drop_index("ix_complaints_user_id", table_name="complaints")
    op.drop_column("complaints", "user_id")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")