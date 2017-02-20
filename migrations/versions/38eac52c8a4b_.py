"""empty message

Revision ID: 38eac52c8a4b
Revises: None
Create Date: 2017-02-18 17:51:03.572521

"""

# revision identifiers, used by Alembic.
revision = '38eac52c8a4b'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('species',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.VARCHAR(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('strain',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.VARCHAR(), nullable=True),
    sa.Column('species_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['species_id'], ['species.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('population',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.VARCHAR(), nullable=True),
    sa.Column('species_id', sa.Integer(), nullable=True),
    sa.Column('source_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['source_id'], ['source.id'], ),
    sa.ForeignKeyConstraint(['species_id'], ['species.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('allele_frequency',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('allele_id', sa.Integer(), nullable=True),
    sa.Column('gene_id', sa.Integer(), nullable=True),
    sa.Column('locus_id', sa.Integer(), nullable=True),
    sa.Column('population_id', sa.Integer(), nullable=True),
    sa.Column('value', sa.FLOAT(), nullable=True),
    sa.Column('source_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['allele_id'], ['allele.id'], ),
    sa.ForeignKeyConstraint(['gene_id'], ['gene.id'], ),
    sa.ForeignKeyConstraint(['locus_id'], ['locus.id'], ),
    sa.ForeignKeyConstraint(['population_id'], ['population.id'], ),
    sa.ForeignKeyConstraint(['source_id'], ['source.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column(u'allele', sa.Column('strain_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'allele', 'strain', ['strain_id'], ['id'])
    op.create_foreign_key('log_file_id', 'analysis', 'file', ['log_file_id'], ['id'], use_alter=True)
    op.create_foreign_key('zip_file_id', 'analysis', 'file', ['zip_file_id'], ['id'], use_alter=True)
    op.create_foreign_key('traceback_file_id', 'analysis', 'file', ['traceback_file_id'], ['id'], use_alter=True)
    op.create_foreign_key('traceback_file_id', 'analysis', 'file', ['settings_file_id'], ['id'], use_alter=True)
    op.add_column(u'gene', sa.Column('locus_name', sa.TEXT(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column(u'gene', 'locus_name')
    op.drop_constraint('traceback_file_id', 'analysis', type_='foreignkey')
    op.drop_constraint('traceback_file_id', 'analysis', type_='foreignkey')
    op.drop_constraint('zip_file_id', 'analysis', type_='foreignkey')
    op.drop_constraint('log_file_id', 'analysis', type_='foreignkey')
    op.drop_constraint(None, 'allele', type_='foreignkey')
    op.drop_column(u'allele', 'strain_id')
    op.drop_table('allele_frequency')
    op.drop_table('population')
    op.drop_table('strain')
    op.drop_table('species')
    ### end Alembic commands ###