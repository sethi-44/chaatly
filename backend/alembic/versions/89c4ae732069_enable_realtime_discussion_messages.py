"""enable_realtime_discussion_messages

Revision ID: 89c4ae732069
Revises: f5b2a3c91e04
Create Date: 2026-07-01 10:10:58.160045

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '89c4ae732069'
down_revision: Union[str, Sequence[str], None] = 'f5b2a3c91e04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable realtime for discussion_messages
    op.execute("ALTER PUBLICATION supabase_realtime ADD TABLE discussion_messages;")


def downgrade() -> None:
    # Disable realtime for discussion_messages
    op.execute("ALTER PUBLICATION supabase_realtime DROP TABLE discussion_messages;")
