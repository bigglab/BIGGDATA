

from flask_wtf import Form
import wtforms
from wtforms.fields import * 
from wtforms.widgets import * 
from wtforms_components import SelectMultipleField 
validators = wtforms.validators 
from wtforms.validators import DataRequired



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
    chain  = SelectField(u'Chain', choices=(['HEAVY', 'HEAVY'], ['LIGHT', 'LIGHT'], ['TCRA', 'TCRA'], ['TCRB', 'TCRB']), validators=[validators.input_required()])

class FileEditForm(Form):
    name = TextField()
    paired_partner = TextField()






