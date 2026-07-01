"""enable_realtime_for_meetups

Revision ID: 47c8c746438b
Revises: 89c4ae732069
Create Date: 2026-07-01 11:53:46.675246

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '47c8c746438b'
down_revision: Union[str, Sequence[str], None] = '89c4ae732069'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Enable realtime for meetups and meetup_participants
    op.execute("ALTER PUBLICATION supabase_realtime ADD TABLE meetups, meetup_participants;")


def downgrade() -> None:
    """Downgrade schema."""
    # Disable realtime
    op.execute("ALTER PUBLICATION supabase_realtime DROP TABLE meetups, meetup_participants;")
