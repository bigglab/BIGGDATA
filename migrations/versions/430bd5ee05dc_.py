"""empty message

Revision ID: 430bd5ee05dc
Revises: 43d5912708fb
Create Date: 2015-11-12 13:30:46.713771

"""

# revision identifiers, used by Alembic.
revision = '430bd5ee05dc'
down_revision = '43d5912708fb'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('dataset',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('name', sa.String(length=256), nullable=True),
    sa.Column('description', sa.String(length=512), nullable=True),
    sa.Column('ig_type', sa.String(length=128), nullable=True),
    sa.Column('paired', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('file',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('dataset_id', sa.Integer(), nullable=True),
    sa.Column('name', sa.String(length=256), nullable=True),
    sa.Column('description', sa.String(length=512), nullable=True),
    sa.Column('file_type', sa.String(length=128), nullable=True),
    sa.Column('path', sa.String(length=256), nullable=True),
    sa.Column('locus', sa.String(length=128), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.Column('paired_partner', sa.Integer(), nullable=True),
    sa.Column('parent', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['dataset_id'], ['dataset.id'], ),
    sa.ForeignKeyConstraint(['paired_partner'], ['file.id'], ),
    sa.ForeignKeyConstraint(['parent'], ['file.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('file')
    op.drop_table('dataset')
    ### end Alembic commands ###