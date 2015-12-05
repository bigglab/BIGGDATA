import os
import json
import static
import time
import random
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from flask_sqlalchemy import SQLAlchemy
from flask_collect import Collect

from app import app, db
from models import * 


app.config.from_pyfile('config.py')

migrate = Migrate(app, db)
manager = Manager(app)
# import models.user 

manager.add_command('db', MigrateCommand)


collectstatic = Collect()
collectstatic.init_app(app)
collectstatic.init_script(manager)
# collectstatic = collect 

if __name__ == '__main__':
    manager.run()



