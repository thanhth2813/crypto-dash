"""initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-02-18

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # holdings
    op.create_table(
        "holdings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("coin_id", sa.String(), nullable=False),
        sa.Column("symbol", sa.String(), nullable=False),
        sa.Column("amount", sa.Numeric(20, 8), nullable=False),
        sa.Column("buy_price", sa.Numeric(20, 8), nullable=False),
        sa.Column("bought_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_holdings_user_id", ondelete="CASCADE"),
    )
    op.create_index("idx_holdings_user", "holdings", ["user_id"], unique=False)

    # alerts
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("coin_id", sa.String(), nullable=False),
        sa.Column("symbol", sa.String(), nullable=False),
        sa.Column("condition", sa.String(), nullable=False),  # above|below
        sa.Column("target", sa.Numeric(20, 8), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default=sa.text("'active'")),
        sa.Column("trigger_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_alerts_user_id", ondelete="CASCADE"),
    )
    op.create_index("idx_alerts_user", "alerts", ["user_id"], unique=False)
    op.create_index("idx_alerts_active", "alerts", ["user_id"], unique=False, postgresql_where=sa.text("status='active'"))

    # price_history
    op.create_table(
        "price_history",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("coin_id", sa.String(), nullable=False),
        sa.Column("symbol", sa.String(), nullable=False),
        sa.Column("timeframe", sa.String(), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Numeric(20, 8), nullable=False),
        sa.Column("high", sa.Numeric(20, 8), nullable=False),
        sa.Column("low", sa.Numeric(20, 8), nullable=False),
        sa.Column("close", sa.Numeric(20, 8), nullable=False),
        sa.Column("volume", sa.Numeric(20, 8), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("coin_id", "timeframe", "ts", name="uq_price_coin_tf_ts"),
    )
    op.create_index("idx_price_history", "price_history", ["coin_id", "timeframe", "ts"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_price_history", table_name="price_history")
    op.drop_table("price_history")

    op.drop_index("idx_alerts_active", table_name="alerts")
    op.drop_index("idx_alerts_user", table_name="alerts")
    op.drop_table("alerts")

    op.drop_index("idx_holdings_user", table_name="holdings")
    op.drop_table("holdings")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
