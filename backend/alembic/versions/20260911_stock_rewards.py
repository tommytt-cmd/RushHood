"""add round-based StockVault index tables

Revision ID: 20260911_stock_rewards
Revises:
Create Date: 2026-09-11
"""

from alembic import op
import sqlalchemy as sa


revision = "20260911_stock_rewards"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stock_tokens",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("token_address", sa.String(42), nullable=False, unique=True),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("name", sa.String(255)), sa.Column("decimals", sa.Integer(), nullable=False),
        sa.Column("logo_url", sa.Text()), sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "round_stocks",
        sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("round_id", sa.Uuid(), sa.ForeignKey("rounds.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stock_token_id", sa.Uuid(), sa.ForeignKey("stock_tokens.id"), nullable=False), sa.Column("eth_spent", sa.Numeric(78, 0)),
        sa.Column("amount_received", sa.Numeric(78, 0), nullable=False, server_default="0"), sa.Column("purchase_tx_hash", sa.String(66)),
        sa.Column("status", sa.String(50), nullable=False, server_default="PENDING"), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("round_id", "stock_token_id", name="uq_round_stock_round_token"),
    )
    op.create_table(
        "stock_rewards",
        sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("round_id", sa.Uuid(), sa.ForeignKey("rounds.id", ondelete="CASCADE"), nullable=False),
        sa.Column("player_id", sa.Uuid(), sa.ForeignKey("players.id", ondelete="CASCADE"), nullable=False), sa.Column("stock_token_id", sa.Uuid(), sa.ForeignKey("stock_tokens.id"), nullable=False),
        *[sa.Column(name, sa.Numeric(78, 0), nullable=False, server_default="0") for name in ("contribution", "total_contribution", "entitlement", "claimed_amount", "claimable_amount")],
        sa.Column("claim_status", sa.String(50), nullable=False, server_default="PENDING"), sa.Column("last_claim_tx_hash", sa.String(66)), sa.Column("claimed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("round_id", "player_id", "stock_token_id", name="uq_stock_reward_round_player_token"),
    )
    op.create_table(
        "stock_claims",
        sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("round_id", sa.Uuid(), sa.ForeignKey("rounds.id"), nullable=False),
        sa.Column("player_id", sa.Uuid(), sa.ForeignKey("players.id"), nullable=False), sa.Column("stock_token_id", sa.Uuid(), sa.ForeignKey("stock_tokens.id"), nullable=False),
        sa.Column("amount", sa.Numeric(78, 0), nullable=False), sa.Column("transaction_hash", sa.String(66), nullable=False, unique=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="CONFIRMED"), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    for table, columns in {"round_stocks": ("round_id", "stock_token_id"), "stock_rewards": ("player_id", "round_id", "stock_token_id"), "stock_claims": ("player_id", "round_id", "transaction_hash")}.items():
        for column in columns:
            op.create_index(f"ix_{table}_{column}", table, [column])


def downgrade() -> None:
    op.drop_table("stock_claims")
    op.drop_table("stock_rewards")
    op.drop_table("round_stocks")
    op.drop_table("stock_tokens")
