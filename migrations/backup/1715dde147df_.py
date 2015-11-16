"""empty message

Revision ID: 1715dde147df
Revises: 1053187ba1b5
Create Date: 2015-10-19 13:30:38.572268

"""

# revision identifiers, used by Alembic.
revision = '1715dde147df'
down_revision = '1053187ba1b5'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('authenticated', sa.Boolean(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'authenticated')
    ### end Alembic commands ###
