"""empty message

Revision ID: 394500ecbeb2
Revises: 3e49124c58cc
Create Date: 2015-11-16 17:56:58.087898

"""

# revision identifiers, used by Alembic.
revision = '394500ecbeb2'
down_revision = '3e49124c58cc'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('file', sa.Column('available', sa.Boolean(), nullable=True))
    op.add_column('file', sa.Column('url', sa.String(length=256), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('file', 'url')
    op.drop_column('file', 'available')
    ### end Alembic commands ###