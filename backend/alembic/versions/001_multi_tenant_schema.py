"""Multi-tenant user tokens and scan history schema.

Revision ID: 001_multi_tenant
Revises:
Create Date: 2026-05-24

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_multi_tenant"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

scan_type_enum = postgresql.ENUM("email", "website", name="scan_type", create_type=False)
threat_status_enum = postgresql.ENUM("safe", "scam", name="threat_status", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "users" not in tables:
        op.create_table(
            "users",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("google_sub", sa.String(length=255), nullable=False),
            sa.Column("email", sa.String(length=320), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=True),
            sa.Column("picture_url", sa.String(length=2048), nullable=True),
            sa.Column("google_access_token", sa.Text(), nullable=True),
            sa.Column("google_refresh_token", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )
        op.create_index("ix_users_google_sub", "users", ["google_sub"], unique=True)
        op.create_index("ix_users_email", "users", ["email"], unique=True)
    else:
        op.execute("DROP TABLE IF EXISTS scan_history CASCADE")
        op.execute("DROP TYPE IF EXISTS scan_status CASCADE")

        if not _column_exists(bind, "users", "google_access_token"):
            op.add_column("users", sa.Column("google_access_token", sa.Text(), nullable=True))

        if _column_exists(bind, "users", "gmail_refresh_token"):
            op.alter_column("users", "gmail_refresh_token", new_column_name="google_refresh_token")
        elif not _column_exists(bind, "users", "google_refresh_token"):
            op.add_column("users", sa.Column("google_refresh_token", sa.Text(), nullable=True))

    scan_type_enum.create(bind, checkfirst=True)
    threat_status_enum.create(bind, checkfirst=True)

    op.execute("DROP TABLE IF EXISTS scan_history CASCADE")

    op.create_table(
        "scan_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", scan_type_enum, nullable=False),
        sa.Column("status", threat_status_enum, nullable=False),
        sa.Column("scanned_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=True),
        sa.Column("result", sa.Text(), nullable=True),
    )
    op.create_index("ix_scan_history_user_id", "scan_history", ["user_id"])
    op.create_index("ix_scan_history_type", "scan_history", ["type"])
    op.create_index("ix_scan_history_scanned_at", "scan_history", ["scanned_at"])
    op.create_index("ix_scan_history_url", "scan_history", ["url"])


def downgrade() -> None:
    op.drop_index("ix_scan_history_url", table_name="scan_history")
    op.drop_index("ix_scan_history_scanned_at", table_name="scan_history")
    op.drop_index("ix_scan_history_type", table_name="scan_history")
    op.drop_index("ix_scan_history_user_id", table_name="scan_history")
    op.drop_table("scan_history")

    bind = op.get_bind()
    if _column_exists(bind, "users", "google_access_token"):
        op.drop_column("users", "google_access_token")
    if _column_exists(bind, "users", "google_refresh_token"):
        op.alter_column("users", "google_refresh_token", new_column_name="gmail_refresh_token")

    threat_status_enum.drop(bind, checkfirst=True)
    scan_type_enum.drop(bind, checkfirst=True)


def _column_exists(bind, table: str, column: str) -> bool:
    inspector = sa.inspect(bind)
    return column in {col["name"] for col in inspector.get_columns(table)}
