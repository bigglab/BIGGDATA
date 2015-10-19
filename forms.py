


import wtforms
from wtforms.fields import * 
from wtforms.form import * 
# Form = wtforms.form.Form 
validators = wtforms.validators 


class LoginForm(Form):
	first_name = StringField(u'First Name', validators=[validators.input_required()])
	last_name  = StringField(u'Last Name', validators=[validators.input_required()])
	email = StringField(u'Email', validators=[validators.input_required()])
	password = PasswordField('password', validators=[validators.input_required()])
	def validate_on_submit(self):
	  print 'validating user login form.... '


