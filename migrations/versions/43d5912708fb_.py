"""empty message

Revision ID: 43d5912708fb
Revises: 1715dde147df
Create Date: 2015-11-12 12:44:37.752090

"""

# revision identifiers, used by Alembic.
revision = '43d5912708fb'
down_revision = '1715dde147df'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('dropbox_path', sa.String(length=256), nullable=True))
    op.add_column('user', sa.Column('scratch_path', sa.String(length=256), nullable=True))
    op.add_column('user', sa.Column('user_type', sa.String(length=128), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'user_type')
    op.drop_column('user', 'scratch_path')
    op.drop_column('user', 'dropbox_path')
    ### end Alembic commands ###
