from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
import os
from flask_sqlalchemy import SQLAlchemy

from app import app
# from app import pgdb as db
db = SQLAlchemy(app)

import app_config
app.config.from_object(app_config)

migrate = Migrate(app, db)
manager = Manager(app)
# import models.user 

manager.add_command('db', MigrateCommand)


# Define our leightweight postgres tables
class User(db.Model):
	__tablename__ = 'user'
	id = db.Column(db.Integer, primary_key=True)
	first_name = db.Column(db.String(128))
	last_name = db.Column(db.String(128))
	email = db.Column(db.String(128))
	password_hash = db.Column(db.String(128))
	data = db.Column(db.Text())
	authenticated = db.Column(db.Boolean, default=False)

	def is_active(self):
	    """True, as all users are active."""
	    return True

	def get_id(self):
	    """Return the email address to satisfy Flask-Login's requirements."""
	    return self.email

	def is_authenticated(self):
	    """Return True if the user is authenticated."""
	    return self.authenticated

	def is_anonymous(self):
	    """False, as anonymous users aren't supported."""
	    return False







if __name__ == '__main__':
    manager.run()



