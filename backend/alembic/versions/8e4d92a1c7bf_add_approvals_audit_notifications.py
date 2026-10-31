"""Add approval targeting, approver permission and in-app notifications."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "8e4d92a1c7bf"
down_revision: Union[str, Sequence[str], None] = "3c81e4b7a912"
branch_labels = None
depends_on = None


def upgrade() -> None:
    user_columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("users")}
    if "can_approve" not in user_columns:
        op.add_column("users", sa.Column("can_approve", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("approvals", sa.Column("action_type", sa.String(length=100), nullable=False, server_default="quotation_review"))
    op.add_column("approvals", sa.Column("target_entity", sa.String(length=100), nullable=False, server_default="quotation"))
    op.add_column("approvals", sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.execute("UPDATE approvals SET target_id = quotation_id WHERE target_id IS NULL")
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recipient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=True),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["recipient_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_recipient_id", "notifications", ["recipient_id"])
    op.create_index("ix_notifications_type", "notifications", ["type"])
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"])


def downgrade() -> None:
    op.drop_index("ix_notifications_is_read", table_name="notifications")
    op.drop_index("ix_notifications_type", table_name="notifications")
    op.drop_index("ix_notifications_recipient_id", table_name="notifications")
    op.drop_table("notifications")
    op.drop_column("approvals", "target_id")
    op.drop_column("approvals", "target_entity")
    op.drop_column("approvals", "action_type")
    op.drop_column("users", "can_approve")
