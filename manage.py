import os
import json
import static
import time
import random
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from flask_sqlalchemy import SQLAlchemy

from app import app, db
from models import * 


app.config.from_pyfile('config.py')

migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)



if __name__ == '__main__':
    manager.run()




