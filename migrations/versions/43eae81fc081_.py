"""empty message

Revision ID: 43eae81fc081
Revises: 2da14eaa0e8a
Create Date: 2015-11-17 16:19:13.604028

"""

# revision identifiers, used by Alembic.
revision = '43eae81fc081'
down_revision = '2da14eaa0e8a'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('file', sa.Column('command', sa.String(length=1024), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('file', 'command')
    ### end Alembic commands ###