"""Add lap_times to RaceResult

Revision ID: 230cd36d182d
Revises: 815032c910a0
Create Date: 2025-04-16 14:31:20.251890

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '230cd36d182d'
down_revision = '815032c910a0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('race_result', schema=None) as batch_op:
        batch_op.add_column(sa.Column('lap_times', sqlite.JSON(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('race_result', schema=None) as batch_op:
        batch_op.drop_column('lap_times')

    # ### end Alembic commands ###
