"""Add age_groups column to Race

Revision ID: 815032c910a0
Revises: 35da2b8bfa82
Create Date: 2025-04-16 12:07:43.002896

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '815032c910a0'
down_revision = '35da2b8bfa82'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('race', schema=None) as batch_op:
        batch_op.add_column(sa.Column('age_groups', sa.Text(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('race', schema=None) as batch_op:
        batch_op.drop_column('age_groups')

    # ### end Alembic commands ###
