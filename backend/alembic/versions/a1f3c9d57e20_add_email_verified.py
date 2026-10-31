"""Add users.email_verified (existing users stay verified)."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a1f3c9d57e20"
down_revision: Union[str, Sequence[str], None] = "8e4d92a1c7bf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_column("users", "email_verified")
