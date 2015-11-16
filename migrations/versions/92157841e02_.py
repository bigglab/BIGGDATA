"""empty message

Revision ID: 92157841e02
Revises: 4d1b2f50ef3b
Create Date: 2015-11-15 21:18:23.449377

"""

# revision identifiers, used by Alembic.
revision = '92157841e02'
down_revision = '4d1b2f50ef3b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('experiment', 'analyses_count')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('experiment', sa.Column('analyses_count', sa.VARCHAR(length=256), autoincrement=False, nullable=True))
    ### end Alembic commands ###
