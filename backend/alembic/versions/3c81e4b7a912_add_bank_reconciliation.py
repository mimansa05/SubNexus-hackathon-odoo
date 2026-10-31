"""add_bank_reconciliation

Revision ID: 3c81e4b7a912
Revises: 66a132f239ce
Create Date: 2026-10-31 13:52:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "3c81e4b7a912"
down_revision: Union[str, Sequence[str], None] = "66a132f239ce"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reconciliation_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("transaction_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("bank_reference", sa.String(length=255), nullable=True),
        sa.Column("transaction_id", sa.String(length=255), nullable=True),
        sa.Column("customer_email", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("deduplication_key", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("match_notes", sa.Text(), nullable=True),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("duplicate_of_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("confirmed_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"], ["customers.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["payment_id"], ["payments.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["invoice_id"], ["invoices.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["duplicate_of_id"],
            ["reconciliation_transactions.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["confirmed_by_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_reconciliation_transactions_transaction_date",
        "reconciliation_transactions",
        ["transaction_date"],
    )
    op.create_index(
        "ix_reconciliation_transactions_status",
        "reconciliation_transactions",
        ["status"],
    )
    op.create_index(
        "ix_reconciliation_transactions_customer_id",
        "reconciliation_transactions",
        ["customer_id"],
    )
    op.create_index(
        "ix_reconciliation_transactions_payment_id",
        "reconciliation_transactions",
        ["payment_id"],
    )
    op.create_index(
        "ix_reconciliation_transactions_invoice_id",
        "reconciliation_transactions",
        ["invoice_id"],
    )
    op.create_index(
        "ix_reconciliation_transactions_confirmed_by_id",
        "reconciliation_transactions",
        ["confirmed_by_id"],
    )
    op.create_index(
        "uq_reconciliation_active_deduplication_key",
        "reconciliation_transactions",
        ["deduplication_key"],
        unique=True,
        postgresql_where=sa.text("status != 'duplicate'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_reconciliation_active_deduplication_key",
        table_name="reconciliation_transactions",
    )
    op.drop_index(
        "ix_reconciliation_transactions_confirmed_by_id",
        table_name="reconciliation_transactions",
    )
    op.drop_index(
        "ix_reconciliation_transactions_invoice_id",
        table_name="reconciliation_transactions",
    )
    op.drop_index(
        "ix_reconciliation_transactions_payment_id",
        table_name="reconciliation_transactions",
    )
    op.drop_index(
        "ix_reconciliation_transactions_customer_id",
        table_name="reconciliation_transactions",
    )
    op.drop_index(
        "ix_reconciliation_transactions_status",
        table_name="reconciliation_transactions",
    )
    op.drop_index(
        "ix_reconciliation_transactions_transaction_date",
        table_name="reconciliation_transactions",
    )
    op.drop_table("reconciliation_transactions")
