"""empty message

Revision ID: 54e4eb34e735
Revises: 563909923e5d
Create Date: 2015-11-17 23:40:34.509253

"""

# revision identifiers, used by Alembic.
revision = '54e4eb34e735'
down_revision = '563909923e5d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('analysis', sa.Column('db_status', sa.String(length=256), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('analysis', 'db_status')
    ### end Alembic commands ###
