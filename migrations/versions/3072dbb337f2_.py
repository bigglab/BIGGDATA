"""empty message

Revision ID: 3072dbb337f2
Revises: None
Create Date: 2016-05-31 16:27:13.565023

"""

# revision identifiers, used by Alembic.
revision = '3072dbb337f2'
down_revision = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

Integer = sa.Integer
String = sa.String

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('project',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('project_name', sa.String(length=128), nullable=True),
    sa.Column('description', sa.String(length=256), nullable=True),
    sa.Column('_id', postgresql.JSON(), nullable=True),
    sa.Column('cell_types_sequenced', sa.String(length=256), nullable=True),
    sa.Column('publications', sa.String(length=256), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('creation_date', sa.DateTime(), nullable=True),
    sa.Column('species', sa.String(length=128), nullable=True),
    sa.Column('lab', sa.String(length=128), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('experiment',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('project_name', sa.String(length=128), nullable=True),
    sa.Column('description', sa.String(length=256), nullable=True),
    sa.Column('_id', postgresql.JSON(), nullable=True),
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
    sa.Column('analyses_settings', postgresql.JSON(), nullable=True),
    sa.Column('lab_notebook_source', sa.String(length=128), nullable=True),
    sa.Column('pairing_technique', sa.String(length=128), nullable=True),
    sa.Column('analyses_count', postgresql.JSON(), nullable=True),
    sa.Column('person_who_prepared_library', sa.String(length=128), nullable=True),
    sa.Column('cell_markers_used', postgresql.ARRAY(String(length=100)), nullable=True),
    sa.Column('list_of_polymerases_used', postgresql.ARRAY(String(length=100)), nullable=True),
    sa.Column('primer_set_name', postgresql.ARRAY(String(length=100)), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user_project',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('read_only', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'project_id')
    )
    op.create_table('dataset',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('project_id', sa.Integer(), nullable=True),
    sa.Column('experiment_id', sa.Integer(), nullable=True),
    sa.Column('name', sa.String(length=256), nullable=True),
    sa.Column('description', sa.String(length=512), nullable=True),
    sa.Column('ig_type', sa.String(length=128), nullable=True),
    sa.Column('paired', sa.Boolean(), nullable=True),
    sa.Column('cell_types_sequenced', postgresql.ARRAY(String(length=50)), nullable=True),
    sa.Column('chain_types_sequenced', postgresql.ARRAY(String(length=20)), nullable=True),
    sa.Column('primary_data_files_ids', postgresql.ARRAY(Integer()), nullable=True),
    sa.Column('lab_notebook_source', sa.String(length=256), nullable=True),
    sa.Column('sequencing_submission_number', sa.String(length=256), nullable=True),
    sa.Column('contains_rna_seq_data', sa.String(length=256), nullable=True),
    sa.Column('reverse_primer_used_in_rt_step', sa.String(length=256), nullable=True),
    sa.Column('list_of_polymerases_used', sa.String(length=256), nullable=True),
    sa.Column('sequencing_platform', sa.String(length=256), nullable=True),
    sa.Column('target_reads', sa.String(length=256), nullable=True),
    sa.Column('cell_markers_used', sa.String(length=256), nullable=True),
    sa.Column('read_access', sa.String(length=256), nullable=True),
    sa.Column('owners_of_experiment', sa.String(length=256), nullable=True),
    sa.Column('adjuvant', sa.String(length=256), nullable=True),
    sa.Column('species', sa.String(length=256), nullable=True),
    sa.Column('cell_selection_kit_name', sa.String(length=256), nullable=True),
    sa.Column('isotypes_sequenced', sa.String(length=256), nullable=True),
    sa.Column('post_sequencing_processing_dict', sa.String(length=512), nullable=True),
    sa.Column('sample_preparation_date', sa.String(length=256), nullable=True),
    sa.Column('gsaf_barcode', sa.String(length=256), nullable=True),
    sa.Column('mid_tag', sa.String(length=256), nullable=True),
    sa.Column('cell_number', sa.String(length=256), nullable=True),
    sa.Column('primer_set_name', sa.String(length=256), nullable=True),
    sa.Column('template_type', sa.String(length=256), nullable=True),
    sa.Column('experiment_name', sa.String(length=256), nullable=True),
    sa.Column('person_who_prepared_library', sa.String(length=256), nullable=True),
    sa.Column('pairing_technique', sa.String(length=256), nullable=True),
    sa.Column('json_id', sa.String(length=256), nullable=True),
    sa.Column('directory', sa.String(length=256), nullable=True),
    sa.ForeignKeyConstraint(['experiment_id'], ['experiment.id'], ),
    sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('project_dataset',
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('dataset_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['dataset_id'], ['dataset.id'], ),
    sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
    sa.PrimaryKeyConstraint('project_id', 'dataset_id')
    )
    op.create_table('analysis',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('zip_file_id', sa.Integer(), nullable=True),
    sa.Column('log_file_id', sa.Integer(), nullable=True),
    sa.Column('traceback_file_id', sa.Integer(), nullable=True),
    sa.Column('settings_file_id', sa.Integer(), nullable=True),
    sa.Column('async_task_id', sa.String(length=128), nullable=True),
    sa.Column('dataset_id', sa.Integer(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('description', sa.String(length=256), nullable=True),
    sa.Column('program', sa.String(), nullable=True),
    sa.Column('started', postgresql.TIMESTAMP(), nullable=True),
    sa.Column('finished', postgresql.TIMESTAMP(), nullable=True),
    sa.Column('params', postgresql.JSON(), nullable=True),
    sa.Column('commands', postgresql.ARRAY(String(length=1024)), nullable=True),
    sa.Column('responses', postgresql.ARRAY(Integer()), nullable=True),
    sa.Column('files_to_analyze', postgresql.ARRAY(Integer()), nullable=True),
    sa.Column('vdj_count', sa.Integer(), nullable=True),
    sa.Column('vj_count', sa.Integer(), nullable=True),
    sa.Column('tcra_count', sa.Integer(), nullable=True),
    sa.Column('tcrb_count', sa.Integer(), nullable=True),
    sa.Column('total_count', sa.Integer(), nullable=True),
    sa.Column('active_command', sa.String(length=512), nullable=True),
    sa.Column('status', sa.String(length=256), nullable=True),
    sa.Column('db_status', sa.String(length=256), nullable=True),
    sa.Column('notes', sa.String(length=1000), nullable=True),
    sa.Column('available', sa.Boolean(), nullable=True),
    sa.Column('inserted_into_db', sa.Boolean(), nullable=True),
    sa.Column('directory', sa.String(length=256), nullable=True),
    sa.Column('error', sa.String(length=256), nullable=True),
    sa.ForeignKeyConstraint(['dataset_id'], ['dataset.id'], ),
    sa.ForeignKeyConstraint(['log_file_id'], ['file.id'], name='log_file_id', use_alter=True),
    sa.ForeignKeyConstraint(['settings_file_id'], ['file.id'], name='traceback_file_id', use_alter=True),
    sa.ForeignKeyConstraint(['traceback_file_id'], ['file.id'], name='traceback_file_id', use_alter=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['zip_file_id'], ['file.id'], name='zip_file_id', use_alter=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('file',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('dataset_id', sa.Integer(), nullable=True),
    sa.Column('name', sa.String(length=256), nullable=True),
    sa.Column('description', sa.String(length=512), nullable=True),
    sa.Column('file_type', sa.String(length=128), nullable=True),
    sa.Column('available', sa.Boolean(), nullable=True),
    sa.Column('in_use', sa.Boolean(), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.Column('path', sa.String(length=256), nullable=True),
    sa.Column('file_size', sa.BigInteger(), nullable=True),
    sa.Column('chain', sa.String(length=128), nullable=True),
    sa.Column('url', sa.String(length=256), nullable=True),
    sa.Column('command', sa.String(length=1024), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.Column('line_count', sa.BigInteger(), nullable=True),
    sa.Column('paired_partner', sa.Integer(), nullable=True),
    sa.Column('parent_id', sa.Integer(), nullable=True),
    sa.Column('analysis_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['analysis_id'], ['analysis.id'], ),
    sa.ForeignKeyConstraint(['dataset_id'], ['dataset.id'], ),
    sa.ForeignKeyConstraint(['paired_partner'], ['file.id'], ),
    sa.ForeignKeyConstraint(['parent_id'], ['file.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('celery_task',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('analysis_id', sa.Integer(), nullable=True),
    sa.Column('async_task_id', sa.String(length=128), nullable=True),
    sa.Column('name', sa.String(length=128), nullable=True),
    sa.Column('result', sa.String(length=512), nullable=True),
    sa.Column('status', sa.String(length=16), nullable=True),
    sa.Column('is_complete', sa.Boolean(), nullable=True),
    sa.Column('failed', sa.Boolean(), nullable=True),
    sa.Column('user_alerted', sa.Boolean(), nullable=True),
    sa.Column('user_dismissed', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['analysis_id'], ['analysis.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('sequence',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('dataset_id', sa.Integer(), nullable=True),
    sa.Column('file_id', sa.Integer(), nullable=True),
    sa.Column('header', sa.String(length=100), nullable=True),
    sa.Column('sequence', sa.String(length=500), nullable=True),
    sa.Column('quality', sa.String(length=500), nullable=True),
    sa.ForeignKeyConstraint(['dataset_id'], ['dataset.id'], ),
    sa.ForeignKeyConstraint(['file_id'], ['file.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('annotation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('sequence_id', sa.Integer(), nullable=True),
    sa.Column('dataset_id', sa.Integer(), nullable=True),
    sa.Column('analysis_id', sa.Integer(), nullable=True),
    sa.Column('_id', postgresql.JSON(), nullable=True),
    sa.Column('seq_id', postgresql.JSON(), nullable=True),
    sa.Column('exp_id', postgresql.JSON(), nullable=True),
    sa.Column('analysis_name', sa.String(), nullable=True),
    sa.Column('strand', sa.String(length=10), nullable=True),
    sa.Column('strand_corrected_sequence', sa.String(), nullable=True),
    sa.Column('read_sequences', sa.String(), nullable=True),
    sa.Column('read_qualities', sa.String(), nullable=True),
    sa.Column('header', sa.String(), nullable=True),
    sa.Column('productive', sa.Boolean(), nullable=True),
    sa.Column('productive_comment', sa.String(length=256), nullable=True),
    sa.Column('recombination_type', sa.String(length=20), nullable=True),
    sa.Column('chain', sa.String(length=20), nullable=True),
    sa.Column('locus', sa.String(), nullable=True),
    sa.Column('isotype', sa.String(), nullable=True),
    sa.Column('isotype_mismatches', sa.Integer(), nullable=True),
    sa.Column('isotype_percent_similarity', sa.FLOAT(), nullable=True),
    sa.Column('isotype_barcode_direction', sa.String(), nullable=True),
    sa.Column('nt', sa.String(length=600), nullable=True),
    sa.Column('aa', sa.String(length=200), nullable=True),
    sa.Column('cdr1_aa', sa.String(length=100), nullable=True),
    sa.Column('cdr1_nt', sa.String(length=100), nullable=True),
    sa.Column('cdr2_aa', sa.String(length=100), nullable=True),
    sa.Column('cdr2_nt', sa.String(length=100), nullable=True),
    sa.Column('cdr3_aa', sa.String(length=200), nullable=True),
    sa.Column('cdr3_nt', sa.String(length=400), nullable=True),
    sa.Column('fr1_nt', sa.String(length=200), nullable=True),
    sa.Column('fr1_aa', sa.String(length=100), nullable=True),
    sa.Column('fr2_nt', sa.String(length=100), nullable=True),
    sa.Column('fr2_aa', sa.String(length=100), nullable=True),
    sa.Column('fr3_nt', sa.String(length=200), nullable=True),
    sa.Column('fr3_aa', sa.String(length=200), nullable=True),
    sa.Column('fr4_nt', sa.String(length=100), nullable=True),
    sa.Column('fr4_aa', sa.String(length=100), nullable=True),
    sa.Column('c_top_hit', sa.String(), nullable=True),
    sa.Column('c_top_hit_locus', sa.String(), nullable=True),
    sa.Column('v_top_hit', sa.String(), nullable=True),
    sa.Column('v_top_hit_locus', sa.String(), nullable=True),
    sa.Column('d_top_hit', sa.String(), nullable=True),
    sa.Column('d_top_hit_locus', sa.String(), nullable=True),
    sa.Column('j_top_hit', sa.String(), nullable=True),
    sa.Column('j_top_hit_locus', sa.String(), nullable=True),
    sa.Column('c_hits', postgresql.JSON(), nullable=True),
    sa.Column('j_hits', postgresql.JSON(), nullable=True),
    sa.Column('d_hits', postgresql.JSON(), nullable=True),
    sa.Column('v_hits', postgresql.JSON(), nullable=True),
    sa.Column('shm_aa', sa.FLOAT(), nullable=True),
    sa.Column('shm_nt', sa.FLOAT(), nullable=True),
    sa.Column('shm_nt_percent', sa.FLOAT(), nullable=True),
    sa.Column('shm_aa_percent', sa.FLOAT(), nullable=True),
    sa.Column('v_shm_nt', sa.Integer(), nullable=True),
    sa.Column('v_shm_percent', sa.FLOAT(), nullable=True),
    sa.Column('j_shm_nt', sa.Integer(), nullable=True),
    sa.Column('j_shm_percent', sa.FLOAT(), nullable=True),
    sa.Column('full_length', sa.Boolean(), nullable=True),
    sa.Column('cdr3_junction_in_frame', sa.Boolean(), nullable=True),
    sa.Column('codon_frame', sa.Integer(), nullable=True),
    sa.Column('start_codon', sa.Integer(), nullable=True),
    sa.Column('stop_codon', sa.Integer(), nullable=True),
    sa.Column('index', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['analysis_id'], ['analysis.id'], ),
    sa.ForeignKeyConstraint(['dataset_id'], ['dataset.id'], ),
    sa.ForeignKeyConstraint(['sequence_id'], ['sequence.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('annotation')
    op.drop_table('sequence')
    op.drop_table('celery_task')
    op.drop_table('file')
    op.drop_table('analysis')
    op.drop_table('project_dataset')
    op.drop_table('dataset')
    op.drop_table('user_project')
    op.drop_table('experiment')
    op.drop_table('project')
    ### end Alembic commands ###
