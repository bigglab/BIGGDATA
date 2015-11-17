

from flask_wtf import Form
import wtforms
from wtforms.fields import * 
from wtforms.widgets import * 
validators = wtforms.validators 
from wtforms.validators import DataRequired



class LoginForm(Form):
	# first_name = StringField(u'First Name', validators=[validators.input_required()])
	# last_name  = StringField(u'Last Name', validators=[validators.input_required()])
	email = StringField('Email', validators=[validators.input_required()])
	password = PasswordField('password', validators=[validators.input_required()])



class RegistrationForm(Form):
	first_name = StringField(u'First Name', validators=[validators.input_required()])
	last_name  = StringField(u'Last Name', validators=[validators.input_required()])
	email = StringField('Email', validators=[validators.input_required()])
	password = PasswordField('password', validators=[validators.input_required()])




class FileUploadForm(Form):
    file     = FileField(u'File Path', validators=[validators.input_required()])
    description  = TextAreaField(u'File Description')
    locus  = TextField(u'IG Loci')
    paired_partner  = IntegerField()
    dataset_id = IntegerField()



class FileDownloadForm(Form):
    url     = TextField(u'File URL', validators=[validators.input_required()], widget=TextInput())
    description  = TextAreaField(u'File Description')
    locus  = TextField(u'IG Loci')
    paired_partner  = IntegerField()
    dataset_id = IntegerField()

