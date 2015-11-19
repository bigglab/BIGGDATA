"""empty message

Revision ID: 2a30473eb01b
Revises: 404f8725e18
Create Date: 2015-11-15 12:33:34.925055

"""

# revision identifiers, used by Alembic.
revision = '2a30473eb01b'
down_revision = '404f8725e18'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import String

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('experiment',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('project_name', sa.String(length=128), nullable=True),
    sa.Column('description', sa.String(length=256), nullable=True),
    sa.Column('paired', sa.Boolean(), nullable=True),
    sa.Column('chain_types_sequenced', postgresql.ARRAY(String(length=20)), nullable=True),
    sa.Column('owners_of_experiment', postgresql.ARRAY(String(length=20)), nullable=True),
    sa.Column('read_access', postgresql.ARRAY(String(length=50)), nullable=True),
    sa.Column('cell_types_sequenced', postgresql.ARRAY(String(length=50)), nullable=True),
    sa.Column('isotypes_sequenced', postgresql.ARRAY(String(length=10)), nullable=True),
    sa.Column('publications', postgresql.ARRAY(String(length=256)), nullable=True),
    sa.Column('mid_tag', postgresql.ARRAY(String(length=256)), nullable=True),
    sa.Column('filenames', postgresql.ARRAY(String(length=256)), nullable=True),
    sa.Column('reverse_primer_used_in_rt_step', sa.String(length=128), nullable=True),
    sa.Column('sample_preparation_date', sa.String(length=128), nullable=True),
    sa.Column('uploaded_by', sa.String(length=128), nullable=True),
    sa.Column('sequencing_platform', sa.String(length=128), nullable=True),
    sa.Column('experiment_creation_date', sa.String(length=128), nullable=True),
    sa.Column('species', sa.String(length=128), nullable=True),
    sa.Column('seq_count', sa.Integer(), nullable=True),
    sa.Column('cell_number', sa.Integer(), nullable=True),
    sa.Column('target_reads', sa.Integer(), nullable=True),
    sa.Column('template_type', sa.String(length=128), nullable=True),
    sa.Column('experiment_name', sa.String(length=256), nullable=True),
    sa.Column('work_order', sa.String(length=128), nullable=True),
    sa.Column('gsaf_sample_name', sa.String(length=128), nullable=True),
    sa.Column('lab', sa.String(length=128), nullable=True),
    sa.Column('cell_selection_kit_name', sa.String(length=128), nullable=True),
    sa.Column('contains_rna_seq_data', sa.Boolean(), nullable=True),
    sa.Column('curated', sa.Boolean(), nullable=True),
    sa.Column('gsaf_barcode', sa.String(length=20), nullable=True),
    sa.Column('lab_notebook_source', sa.String(length=128), nullable=True),
    sa.Column('pairing_technique', sa.String(length=128), nullable=True),
    sa.Column('analyses_count', sa.String(length=256), nullable=True),
    sa.Column('person_who_prepared_library', sa.String(length=128), nullable=True),
    sa.Column('cell_markers_used', postgresql.ARRAY(String(length=100)), nullable=True),
    sa.Column('list_of_polymerases_used', postgresql.ARRAY(String(length=100)), nullable=True),
    sa.Column('primer_set_name', postgresql.ARRAY(String(length=100)), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column(u'dataset', sa.Column('experiment_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'dataset', 'experiment', ['experiment_id'], ['id'])
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'dataset', type_='foreignkey')
    op.drop_column(u'dataset', 'experiment_id')
    op.drop_table('experiment')
    ### end Alembic commands ###