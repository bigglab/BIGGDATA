"""empty message

Revision ID: 8fa97a2b0fd
Revises: 533232921388
Create Date: 2015-11-19 13:14:49.183596

"""

# revision identifiers, used by Alembic.
revision = '8fa97a2b0fd'
down_revision = '533232921388'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('file', sa.Column('chain', sa.String(length=128), nullable=True))
    op.add_column('file', sa.Column('s3_available', sa.Boolean(), nullable=True))
    op.add_column('file', sa.Column('s3_status', sa.String(length=50), nullable=True))
    op.add_column('file', sa.Column('status', sa.String(length=50), nullable=True))
    op.drop_column('file', 'transfer_status')
    op.drop_column('file', 'locus')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('file', sa.Column('locus', sa.VARCHAR(length=128), autoincrement=False, nullable=True))
    op.add_column('file', sa.Column('transfer_status', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_column('file', 'status')
    op.drop_column('file', 's3_status')
    op.drop_column('file', 's3_available')
    op.drop_column('file', 'chain')
    ### end Alembic commands ###