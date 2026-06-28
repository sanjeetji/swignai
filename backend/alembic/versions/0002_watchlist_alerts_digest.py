"""watchlists + price_alerts tables, user_preferences.email_digest column.

Retention layer (blueprint/13): watchlists, custom price alerts, digest email opt-in.

Revision ID: 0002_watchlist_alerts_digest
Revises: 0001_baseline
Create Date: 2026-06-28
"""
import sqlalchemy as sa
from alembic import op

revision = "0002_watchlist_alerts_digest"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "watchlists",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False),
        sa.Column("symbol", sa.String(length=32), index=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("user_id", "symbol", name="uq_watch_user_symbol"),
    )
    op.create_table(
        "price_alerts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False),
        sa.Column("symbol", sa.String(length=32), index=True, nullable=False),
        sa.Column("direction", sa.String(length=6), nullable=False),
        sa.Column("target_price", sa.Float(), nullable=False),
        sa.Column("is_active", sa.Boolean(), index=True, nullable=False, server_default=sa.true()),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("user_preferences",
                  sa.Column("email_digest", sa.Boolean(), nullable=False, server_default=sa.true()))


def downgrade() -> None:
    op.drop_column("user_preferences", "email_digest")
    op.drop_table("price_alerts")
    op.drop_table("watchlists")
