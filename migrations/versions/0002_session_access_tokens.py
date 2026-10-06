"""Bind chat sessions to a server-issued access token."""

from alembic import op
import sqlalchemy as sa

revision = "0002_session_access_tokens"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("chat_sessions", sa.Column("access_token", sa.String(length=128), nullable=True))
    op.create_index("uq_chat_sessions_access_token", "chat_sessions", ["access_token"], unique=True)


def downgrade() -> None:
    op.drop_index("uq_chat_sessions_access_token", table_name="chat_sessions")
    op.drop_column("chat_sessions", "access_token")
