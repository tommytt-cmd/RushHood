"""add StockVault indexer checkpoint

Revision ID: 20260911_stock_indexer_checkpoint
Revises: 20260911_stock_rewards
Create Date: 2026-09-11
"""

from alembic import op
import sqlalchemy as sa


revision = "20260911_stock_indexer_checkpoint"
down_revision = "20260911_stock_rewards"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stock_indexer_checkpoints",
        sa.Column("vault_address", sa.String(length=42), primary_key=True),
        sa.Column("last_indexed_block", sa.BigInteger(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("stock_indexer_checkpoints")
