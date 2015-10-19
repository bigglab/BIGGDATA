

from flask_wtf import Form
from wtforms import TextField, PasswordField, SelectField
import wtforms
from wtforms.fields import * 
validators = wtforms.validators 
from wtforms.validators import DataRequired



class LoginForm(Form):
	# first_name = StringField(u'First Name', validators=[validators.input_required()])
	# last_name  = StringField(u'Last Name', validators=[validators.input_required()])
	email = StringField('Email', validators=[validators.input_required()])
	password = PasswordField('password', validators=[validators.input_required()])



class CreateUserForm(Form):
	first_name = StringField(u'First Name', validators=[validators.input_required()])
	last_name  = StringField(u'Last Name', validators=[validators.input_required()])
	email = StringField('Email', validators=[validators.input_required()])
	password = PasswordField('password', validators=[validators.input_required()])



	
