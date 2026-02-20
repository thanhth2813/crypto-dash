"""add risk_config to trading_bots

Revision ID: 034c607b6fb1
Revises: ad40e15767a6
Create Date: 2026-02-20 11:50:03.520925

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '034c607b6fb1'
down_revision = 'ad40e15767a6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add risk_config column with default value
    op.execute("""
        ALTER TABLE trading_bots 
        ADD COLUMN risk_config JSON NOT NULL 
        DEFAULT '{"max_position_usd": 100, "max_daily_loss_pct": 10, "max_consecutive_losses": 5, "max_drawdown_pct": 15}'::json
    """)


def downgrade() -> None:
    op.drop_column('trading_bots', 'risk_config')
