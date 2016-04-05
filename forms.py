

from flask_wtf import Form

from datetime import datetime

import wtforms
from wtforms.fields import * 
from wtforms.widgets import * 
from wtforms.validators import DataRequired

validators = wtforms.validators 



class LoginForm(Form):
	# first_name = StringField(u'First Name', validators=[validators.input_required()])
	# last_name  = StringField(u'Last Name', validators=[validators.input_required()])
	email = StringField('Email', validators=[validators.input_required()])
	password = PasswordField('password', validators=[validators.input_required()])



class RegistrationForm(Form):
    username = StringField(u'Username', validators=[validators.input_required()])
    first_name = StringField(u'First Name', validators=[validators.input_required()])
    last_name  = StringField(u'Last Name', validators=[validators.input_required()])
    email = StringField('Email', validators=[validators.input_required()])
    password = PasswordField('password', validators=[validators.input_required()])


class CreateMixcrAnalysisForm(Form): 
    dataset_id = IntegerField()
    name = TextField(u'Name')
    description = TextField(u'Description')
    trim = BooleanField(u'Trim Illumina Adapters')
    pair_overlaps = BooleanField(u'Pair Overlaps')
    pair_interchain = BooleanField(u'Pair Interchain')
    insert_into_db = BooleanField(u'Insert Into DB')
    cluster = BooleanField(u'Cluster Sequences')


class CreatePandaseqAnalysisForm(Form): 
    dataset_id = IntegerField()
    name = TextField(u'Name', )
    description = TextField(u'Description')
    algorithm = SelectField(u'Algorithm', choices=(['ea_util', 'ea_util'], ['flash', 'flash'], ['pear', 'pear'], ['rdp_mle', 'rdp_mle'],  ['simple_bayesian', 'simple_bayesian'], ['stitch', 'stitch'], ['uparse', 'uparse']), validators=[validators.input_required()])



class FileDownloadForm(Form):
    url     = TextField(u'File URL', validators=[validators.input_required()], widget=TextInput())
    description  = TextAreaField(u'File Description')
    chain  = SelectField(u'Chain', choices=(['HEAVY', 'HEAVY'], ['LIGHT', 'LIGHT'], ['HEAVY/LIGHT', 'HEAVY/LIGHT'], ['TCRA', 'TCRA'], ['TCRB', 'TCRB'], ['TCRA/B', 'TCRA/B']), validators=[validators.input_required()])
    paired_partner  = IntegerField()
    dataset_id = IntegerField()


class FileUploadForm(Form):
    file     = FileField(u'File Path', validators=[validators.input_required()])
    description  = TextAreaField(u'File Description')
    chain  = SelectField(u'Chain', choices=(['HEAVY', 'HEAVY'], ['LIGHT', 'LIGHT'], ['TCRA', 'TCRA'], ['TCRB', 'TCRB']), validators=[validators.input_required()])
    paired_partner  = IntegerField()
    dataset_id = IntegerField()


class AssociateFilesToDatasetForm(Form):
    file_ids  = SelectField(u'Files', coerce=int)
    dataset_id = IntegerField()
    submit = SubmitField()



class CreateDatasetForm(Form):
    name = TextField()
    description = TextField()
    paired = BooleanField()
    ig_type = TextField()
    # experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id'))
    # files = db.relationship('File', backref='dataset', lazy='dynamic')
    # sequences = db.relationship('Sequence', backref='dataset', lazy='dynamic')
    # analyses = db.relationship('Analysis', backref='dataset', lazy='dynamic')
    # annotations = db.relationship('Annotation', backref='dataset', lazy='dynamic')

class ImportSraAsDatasetForm(Form):
    accession = TextField()
    description = TextField()
    chain  = SelectField(u'Chain', choices=(['HEAVY', 'HEAVY'], ['LIGHT', 'LIGHT'], ['HEAVY/LIGHT', 'HEAVY/LIGHT'], ['TCRA', 'TCRA'], ['TCRB', 'TCRB'], ['TCRA/B', 'TCRA/B']), validators=[validators.input_required()])

class FileEdit(Form):
    name = TextField()
    paired_partner = TextField()

class CreateProjectForm(Form):

        #Notes: 
        user_id = 'user.id'
        project_name = TextField('Project Name', [validators.required(), validators.length(max=128)])
        description = TextAreaField('Project Description', [validators.length(max=256)])

        cell_types_sequenced = TextField('Cell Types Sequenced', [validators.length(max=50)])
        
        publications = TextField('Publications', [validators.length(max=256)])

        # species = db.Column(db.String(128))
        species = TextField('Species', [validators.length(max=128)])

        # lab = db.Column(db.String(128))
        lab = TextField('Lab', [validators.length(max=128)], default = 'Georgiou')


        #isotypes_sequenced_a = BooleanField('IgA')
        #isotypes_sequenced_g = BooleanField('IgG')
        #isotypes_sequenced_k = BooleanField('IgK')
        #isotypes_sequenced_l = BooleanField('IgL')
        #isotypes_sequenced_m = BooleanField('IgM')
        
        # experiment_name = db.Column(db.String(256))
        # experiment_name = TextField('Experiment Name', [validators.required(), validators.length(max=256)])

        #paired = BooleanField('Paired')

        # chain_types_heavy = BooleanField('Heavy')
        # chain_types_heavy = BooleanField('Light')
        
        # we should leave this column in temporarily for compatibility
        # as soon as the association table is created we can remove this column
        # TO DO: create new user accounts for every user listed in this column
        
        #owners_of_experiment = db.Column(postgresql.ARRAY(db.String(20)))
        #read_access = db.Column(postgresql.ARRAY(db.String(50)))

        #mid_tag = TextField('Mid Tag', [validators.required(), validators.length(max=256)])
        
        # Filenames will become datasets, to be added later
        # filenames = db.Column(postgresql.ARRAY(db.String(256)))

        #reverse_primer_used_in_rt_step = TextField('Reverse Primer Used in RT Step', [validators.required(), validators.length(max=128)])
        
        #sample_preparation_date = DateField('Sample Preparation Date (mm/dd/yyyy)', default=datetime.today, format='%m/%d/%Y')

        # uploaded_by = db.Column(db.String(128))
        # Set this to the current user?

        # sequencing_platform = db.Column(db.String(128))
        #sequencing_platform = TextField('Sequencing Platform', [validators.required(), validators.length(max=128)])

        # experiment_creation_date = db.Column(db.String(128))
        # Is this the current date?


        # seq_count = db.Column(db.Integer())
        #seq_count = IntegerField('Sequence Count', [validators.required()] )

        # cell_number = db.Column(db.Integer())
        #cell_number = IntegerField('Cell Number', [validators.required()] )
        
        # target_reads = db.Column(db.Integer())
        #target_reads = IntegerField('Target Reads', [validators.required()] )
        
        # template_type = db.Column(db.String(128))
        #template_type = TextField('Template Type', [validators.required(), validators.length(max=128)])

        # work_order = db.Column(db.String(128))
        #work_order = TextField('Work Order', [validators.required(), validators.length(max=128)])
        
        # gsaf_sample_name = db.Column(db.String(128))
        #gsaf_sample_name = TextField('GSAF Sample Name',[validators.required(), validators.length(max=128)])


        # cell_selection_kit_name = db.Column(db.String(128))
        #cell_selection_kit_name = TextField('Cell Selection Kit Name', [validators.required(), validators.length(max=128)])
        
        # contains_rna_seq_data = db.Column(db.Boolean, default=False)
        #contains_rna_seq_data = BooleanField('Contains RNA Sequence DNA', [validators.required()])

        # curated = db.Column(db.Boolean, default=False)
        # curated = BooleanField('Curated', [validators.required()])
        
        # gsaf_barcode = db.Column(db.String(20))
        #gsaf_barcode = TextField('GSAF Barcode', [validators.required(), validators.length(max=20)])

        # analyses_settings = db.Column(JSON())
        # how is this populated?

        # lab_notebook_source = db.Column(db.String(128))
        #lab_notebook_source = TextField('Lab Notebook Source', [validators.required(), validators.length(max=128)])
        
        # pairing_technique = db.Column(db.String(128))
        #pairing_technique = TextField('Pairing Technique', [validators.required(), validators.length(max=128)])
        
        # analyses_count = db.Column(JSON())
        # how is this populated

        # person_who_prepared_library = db.Column(db.String(128))
        #person_who_prepared_library = TextField('Person Who Prepared Library', [validators.required(), validators.length(max=128)])

        # cell_markers_used = db.Column(postgresql.ARRAY(db.String(100)))
        #cell_markers_used = TextField('Cell Markers Used', [validators.required(), validators.length(max=128)])

        # list_of_polymerases_used = db.Column(postgresql.ARRAY(db.String(100)))
        #list_of_polymerases_used = TextField('List of Polymerases Used', [validators.required(), validators.length(max=128)])

        # primer_set_name = db.Column(postgresql.ARRAY(db.String(100)))
        #primer_set_name = TextField('Primer Set Name', [validators.required(), validators.length(max=128)])
        
        # datasets = db.relationship('Dataset', backref='experiment', lazy='dynamic')
        # use a multiselect for this?

        # establish a relationship to the association table
        #users = db.relationship('User', secondary = user_experiments, back_populates = 'experiments' )




