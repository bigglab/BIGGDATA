"""empty message

Revision ID: 9923834ba0
Revises: 146cd67f2d78
Create Date: 2016-03-28 14:10:55.934746

"""

# revision identifiers, used by Alembic.
revision = '9923834ba0'
down_revision = '146cd67f2d78'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('annotation', sa.Column('index', sa.Integer(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('annotation', 'index')
    ### end Alembic commands ###