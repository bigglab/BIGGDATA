

from flask_wtf import Form
#from flask.ext.wtf import widgets

from datetime import datetime

import wtforms
from wtforms.fields import * 
from wtforms.widgets import * 
from wtforms.validators import DataRequired
from wtforms import widgets

validators = wtforms.validators 

class MultiCheckboxField(SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class LoginForm(Form):
	# first_name = StringField(u'First Name', validators=[validators.input_required()])
	# last_name  = StringField(u'Last Name', validators=[validators.input_required()])
	email = StringField('Email', validators=[validators.input_required()])
	password = PasswordField('Password', validators=[validators.input_required()])

class RegistrationForm(Form):
    username = StringField(u'Username', validators=[validators.input_required()])
    first_name = StringField(u'First Name', validators=[validators.input_required()])
    last_name  = StringField(u'Last Name', validators=[validators.input_required()])
    email = StringField('Email', validators=[validators.input_required()])
    password = PasswordField('Password', validators=[validators.input_required()])



class CreatePandaseqAnalysisForm(Form): 
    dataset_id = IntegerField()
    name = TextField(u'Name', )
    description = TextField(u'Description')
    minimum_overlap = IntegerField(u'Minimum Overlap', default=10)
    minimum_length = IntegerField(u'Minimum Consensus Length', default=100)
    file_ids = SelectMultipleField(u'Files To Collapse')
    algorithm = SelectField(u'Algorithm', choices=(['ea_util', 'ea_util'], ['flash', 'flash'], ['pear', 'pear'], ['rdp_mle', 'rdp_mle'],  ['simple_bayesian', 'simple_bayesian'], ['stitch', 'stitch'], ['uparse', 'uparse']), validators=[validators.input_required()])


class CreateMSDBAnalysisForm(Form): 
    dataset_ids = MultiCheckboxField('Datasets', choices=[])
    file_ids = MultiCheckboxField('Datasets', choices=[])
    dataset_id = IntegerField()
    name = TextField(u'Name', )
    description = TextField(u'Description')
    msdb_cluster_percent = DecimalField(places=2, rounding=None, default = 0.90)
    msdb_cluster_algorithm = SelectField(u'Cluster Algorithm', choices=[('greedy', 'Greedy'), ('agglomerative', 'Agglomerative')], validators=[validators.input_required()])
    msdb_cluster_linkage = SelectField(u'Cluster Linkage', choices=[('min', 'min'), ('avg', 'avg'), ('max', 'max')], validators=[validators.input_required()])
    require_annotations = MultiCheckboxField('Require Annotations', choices=[('aaSeqFR1', 'FR1'),('aaSeqCDR1', 'CDR1'),('aaSeqFR2', 'FR2'),('aaSeqCDR2', 'CDR2'),('aaSeqFR3', 'FR3'),('aaSeqCDR3', 'CDR3'),('aaSeqFR4', 'FR4')], default = ['aaSeqCDR3'])
    read_cutoff = IntegerField(default=1)
    cluster_on = SelectField('Cluster On', choices=[('nSeqCDR3', 'CDR3 NT'),('aaSeqCDR3', 'CDR3 AA'),('aaFullSeq', 'Full AA'), ('nFullSeq', 'Full NT')], default = 'aaSeqCDR3')
    append_cterm_peptides = BooleanField(default=False)


class AssociateFilesToDatasetForm(Form):
    file_ids  = SelectField(u'Files', coerce=int)
    dataset_id = IntegerField()
    submit = SubmitField()

class CreateDatasetForm(Form):
    use_as_default = BooleanField('Use These Values as Defaults')

    dataset_id = IntegerField()
    name = TextField()
    description = TextField()
    paired = BooleanField()
    ig_type = TextField()
    project  = SelectField(u'Project', choices=[('new', 'New Project')], validators=[validators.input_required()])
    cell_types_sequenced = TextField('Cell Types Sequenced (Array)')
    chain_types_sequenced = TextField('Chain Types Sequenced (Array)')
    primary_data_files_ids = TextField('Primary Data Files Ids (Array)')
    lab_notebook_source = TextField()
    sequencing_submission_number = TextField()
    contains_rna_seq_data = TextField()
    reverse_primer_used_in_rt_step = TextField()
    list_of_polymerases_used = TextField()
    sequencing_platform = TextField()
    target_reads = TextField()
    cell_markers_used = TextField()
    read_access = TextField()
    owners_of_experiment = TextField()
    adjuvant = TextField()
    species = TextField()
    cell_selection_kit_name = TextField()
    isotypes_sequenced = TextField()
    post_sequencing_processing_dict = TextField()
    sample_preparation_date = TextField()
    gsaf_barcode = TextField()
    mid_tag = TextField()
    cell_number = TextField()
    primer_set_name = TextField()
    template_type = TextField()
    experiment_name = TextField()
    person_who_prepared_library = TextField()
    pairing_technique = TextField()
    json_id = TextField()


class EditDatasetForm(Form):
    use_as_default = BooleanField('Use These Values as Defaults')

    dataset_id = IntegerField()

    name = TextField()
    description = TextField()
    paired = BooleanField()
    ig_type = TextField()

    cell_types_sequenced = TextField('Cell Types Sequenced (Array)')
    chain_types_sequenced = TextField('Chain Types Sequenced (Array)')
    primary_data_files_ids = TextField('Primary Data Files Ids (Array)')

    lab_notebook_source = TextField()
    sequencing_submission_number = TextField()
    contains_rna_seq_data = TextField()
    reverse_primer_used_in_rt_step = TextField()
    list_of_polymerases_used = TextField()
    sequencing_platform = TextField()
    target_reads = TextField()
    cell_markers_used = TextField()
    read_access = TextField()
    owners_of_experiment = TextField()
    adjuvant = TextField()

    #species = TextField('Species', [validators.length(max=128)])
    species = SelectField( 'Species', choices=[('', ''), ('H. sapiens', 'H. sapiens'), ('M. musculus', 'M. musculus')] )

    cell_selection_kit_name = TextField()
    isotypes_sequenced = TextField()
    post_sequencing_processing_dict = TextField()
    sample_preparation_date = TextField()
    gsaf_barcode = TextField()
    mid_tag = TextField()
    cell_number = TextField()
    primer_set_name = TextField()
    template_type = TextField()
    experiment_name = TextField()
    person_who_prepared_library = TextField()
    pairing_technique = TextField()
    json_id = TextField()


class FileEditForm(Form):
    name = TextField('File Name', [validators.length(max=256)])
    description = TextField('Description', [validators.length(max=256)])
    paired_partner = SelectField('Paired partner', coerce=int)
    chain  = SelectField('Chain', choices=(('HEAVY', 'HEAVY'), ('LIGHT', 'LIGHT'), ('HEAVY/LIGHT', 'HEAVY/LIGHT'), ('TCRA', 'TCRA'), ('TCRB', 'TCRB'), ('TCRA/B', 'TCRA/B')))
    file_type  = SelectField('File Type', choices=())

class CreateProjectForm(Form):
    user_id = 'user.id'
    project_name = TextField('Project Name', [validators.required(), validators.length(max=128)])
    description = TextAreaField('Project Description', [validators.length(max=256)])
    cell_types_sequenced = TextField('Cell Types Sequenced', [validators.length(max=50)])        
    publications = TextField('Publications', [validators.length(max=256)])
    lab = TextField('Lab', [validators.length(max=128)], default = 'Georgiou')
    editors = SelectMultipleField('Modify Users Who Can Edit', choices=[('None','None')])
    viewers = SelectMultipleField('Modify Users Who Can View', choices=[('None','None')])
    datasets = SelectMultipleField('Add Existing Datasets to Project', choices=[('None','None')])

    file = FileField(u'Add Datasets from JSON File')
    url = TextField(u'JSON URL')

    #species = TextField('Species', [validators.length(max=128)])
    species = SelectField( 'Species', choices=[('', ''), ('H. sapiens', 'H. sapiens'), ('M. musculus', 'M. musculus')] )


class MultiCheckboxField(SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """
    widget = wtforms.widgets.ListWidget(prefix_label=False)
    option_widget = wtforms.widgets.CheckboxInput()


class ImportFilesForm(Form): 

    file_source = RadioField('Select a File Source', choices=[ ('file_dataset' , 'Files from Dataset'), ('file_gsaf' , 'Files from GSAF URL'), ('file_upload' , 'Upload Files'), ('file_url' , 'File from URL'), ('file_ncbi' , 'Files from NCBI') ])

    local_file_1 = FileField(u'Local File Path')
    local_file_2 = FileField(u'Local File Path')
    
    server_file_1 = TextField(u'File Path', validators=[validators.input_required()], widget=TextInput())
    server_file_2 = TextField(u'File Path', validators=[validators.input_required()], widget=TextInput())

    file_pairing = SelectField(u'File Pairing (2 files required)', choices = [ ('none','None'), ('vhvl','Heavy/Light Chain Pairing'), ('forev','Forward/Reverse Pairing') ] )

    ncbi_accession = TextField()

    download_url_1  = TextField(u'File URL', validators=[validators.input_required()], widget=TextInput())
    download_url_2  = TextField(u'File URL', validators=[validators.input_required()], widget=TextInput())

    gsaf_url  = TextField(u'GSAF URL', validators=[validators.input_required()], widget=TextInput())

    output_dataset  = SelectField(u'Add to Dataset', choices=[('new', 'New Dataset')], validators=[validators.input_required()])
    output_project  = SelectField(u'Project', choices=[('new', 'New Project')], validators=[validators.input_required()])
    
    dataset_name = TextField(u'Dataset Name', )
    dataset_description = TextField(u'Dataset Description')
    project_name = TextField(u'Project Name', )
    project_description = TextField(u'Project Description')

    chain  = SelectField(u'Chain', choices=(['HEAVY', 'HEAVY'], ['LIGHT', 'LIGHT'], ['HEAVY/LIGHT', 'HEAVY/LIGHT'], ['TCRA', 'TCRA'], ['TCRB', 'TCRB'], ['TCRA/B', 'TCRA/B']), validators=[validators.input_required()])





class BuildPipelineForm(Form):
    file_source = RadioField('Select a File Source', choices=[ ('file_dataset' , 'Files from Dataset'), ('file_gsaf' , 'Files from GSAF URL'), ('file_upload' , 'Upload Files'), ('file_url' , 'File from URL'), ('file_ncbi' , 'Files from NCBI') ])

    file_pairing = SelectField(u'File Pairing (2 files required)', choices = [ ('none','None'), ('vhvl','Heavy/Light Chain Pairing'), ('forev','Forward/Reverse Pairing') ] )

    name = TextField(u'Name', )
    description = TextField(u'Description')

    dataset = SelectMultipleField(u'Select Dataset', choices = [ ('','') ] )
    dataset_files = SelectMultipleField(u'Select Files', choices = [ ('','') ])

    trim = BooleanField(u'Trim Illumina Adapters')
    trim_slidingwindow = BooleanField(u'Use Sliding Window Trimming', default=False) # Perform a sliding window trimming, cutting once the average quality within the window falls below a threshold.
    trim_slidingwindow_size = IntegerField(u'Window Size (Integer)', default=4) # windowSize: specifies the number of bases to average across
    trim_slidingwindow_quality = IntegerField(u'Required Quality (Integer)', default=15) # requiredQuality: specifies the average quality required.
    trim_illumina_adapters = BooleanField(u'Trim Illumina Adapters', default=True)

    filter = BooleanField(u'Quality Filter Reads', default='checked')
    filter_quality = IntegerField(u'Minimum Quality', default=20)
    filter_percentage = IntegerField(u'Read Percentage', default=50)

    pandaseq = BooleanField('PANDAseq')
    pandaseq_algorithm = SelectField(u'PANDAseq Algorithm', choices=(['ea_util', 'ea_util'], ['flash', 'flash'], ['pear', 'pear'], ['rdp_mle', 'rdp_mle'],  ['simple_bayesian', 'simple_bayesian'], ['stitch', 'stitch'], ['uparse', 'uparse']), validators=[validators.input_required()])
    pandaseq_minimum_overlap = IntegerField(u'Minimum Overlap', default=10)
    pandaseq_minimum_length = IntegerField(u'Minimum Consensus Length', default=100)

    analysis_type = RadioField('Select a File Source', choices=[ ('igrep' , 'IGREP/IGFFT'), ('mixcr' , 'MixCR'), ('abstar' , 'ABStar')])

    loci = MultiCheckboxField('Loci', choices=[('IGH', 'IGH'), ('IGL', 'IGL'), ('IGK', 'IGK'), ('TCRA', 'TCRA'), ('TCRB', 'TCRB') ,('TCRG', 'TCRG'), ('TCRD', 'TCRD')], default = ['IGH', 'IGK', 'IGL'])
    species = SelectField( 'Species', choices=[('H. sapiens', 'H. sapiens'), ('M. musculus', 'M. musculus')] )

    standardize_outputs = BooleanField('Standardize Output', default='checked')
    require_annotations = MultiCheckboxField('Require Annotations', choices=[('aaSeqFR1', 'FR1'),('aaSeqCDR1', 'CDR1'),('aaSeqFR2', 'FR2'),('aaSeqCDR2', 'CDR2'),('aaSeqFR3', 'FR3'),('aaSeqCDR3', 'CDR3'),('aaSeqFR4', 'FR4')], default = ['aaSeqCDR3'])

    remove_seqs_with_indels = BooleanField('Remove Sequences With Indels', default='checked')
    append_cterm_peptides = BooleanField('Append Peptides to C-Term for Mass Spec') # , default='checked')

    cluster = BooleanField(u'Cluster Sequences')
    generate_msdb = BooleanField(u'Generate Mass Spec Database')
    pair_vhvl = BooleanField(u'VH/VL Paired Data', default=False)

    msdb_cluster_percent = DecimalField('Cluster Percent (MSDB)', places=2, rounding=None, default = 0.9)

    vhvl_min = DecimalField('VH/VL Min', places=2, rounding=None, default = 0.96)
    vhvl_max = DecimalField('VH/VL Max', places=2, rounding=None, default = 0.96)
    vhvl_step = DecimalField('VH/VL Step', places=2, rounding=None, default = 0.0   )


