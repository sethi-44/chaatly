"""add discussion_message indexes

Revision ID: f5b2a3c91e04
Revises: d30112cabab9
Create Date: 2026-07-01 09:38:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'f5b2a3c91e04'
down_revision: Union[str, Sequence[str], None] = 'd30112cabab9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index('ix_discussion_messages_meetup_id', 'discussion_messages', ['meetup_id'])
    op.create_index('ix_discussion_messages_user_id', 'discussion_messages', ['user_id'])
    op.create_index('ix_discussion_messages_created_at', 'discussion_messages', ['created_at'])
    op.create_index('ix_discussion_messages_parent_message_id', 'discussion_messages', ['parent_message_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_discussion_messages_parent_message_id', table_name='discussion_messages')
    op.drop_index('ix_discussion_messages_created_at', table_name='discussion_messages')
    op.drop_index('ix_discussion_messages_user_id', table_name='discussion_messages')
    op.drop_index('ix_discussion_messages_meetup_id', table_name='discussion_messages')
