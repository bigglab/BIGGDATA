import os
import json
import static
import time
import random
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
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


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(128))
    last_name = db.Column(db.String(128))
    email = db.Column(db.String(128))
    password_hash = db.Column(db.String(128))
    data = db.Column(db.Text())
    authenticated = db.Column(db.Boolean, default=False)
    user_type = db.Column(db.String(128))
    dropbox_path = db.Column(db.String(256))
    scratch_path = db.Column(db.String(256))

    # @classmethod
    # def find_by_email(self, email):
    #     unvalidated_response = db.session.query(User).filter_by(email=email).all()
    #     return unvalidated_response[0]

    def get_id(self):
        """Return the email address to satisfy Flask-Login's requirements."""
        return self.email

    def is_active(self):
        """True, as all users are active."""
        return True

    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return self.authenticated

    def is_anonymous(self):
        """False, as anonymous users aren't supported."""
        return False




class File(db.Model):
		__tablename__ = 'file'
		id = db.Column(db.Integer, primary_key=True)
		user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
		dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'))
		name = db.Column(db.String(256))
		description =db.Column(db.String(512))
		file_type = db.Column(db.String(128))
		path = db.Column(db.String(256))
		locus = db.Column(db.String(128))
		created = db.Column(db.DateTime, default=db.func.now())
		paired_partner = db.Column(db.Integer, db.ForeignKey('file.id'))
		parent = db.Column(db.Integer, db.ForeignKey('file.id'))


class Dataset(db.Model):
		__tablename__ = 'dataset'
		id = db.Column(db.Integer, primary_key=True)
		user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
		name = db.Column(db.String(256))
		description =db.Column(db.String(512))
		ig_type = db.Column(db.String(128))
		paired = db.Column(db.Boolean, default=False)




if __name__ == '__main__':
    manager.run()



