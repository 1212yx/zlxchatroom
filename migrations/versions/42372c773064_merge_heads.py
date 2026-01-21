"""Merge heads

Revision ID: 42372c773064
Revises: 1a3fb5c954b5, 219612da2cea, 92ae2a8635e2, e1c49be97fc7
Create Date: 2026-01-21 09:02:12.087336

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '42372c773064'
down_revision = ('1a3fb5c954b5', '219612da2cea', '92ae2a8635e2', 'e1c49be97fc7')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
