import os
import json
import static
import time
import random
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from flask_sqlalchemy import SQLAlchemy

from app import app, db
# from app import pgdb as db
# db = SQLAlchemy(app)

import app_config
app.config.from_object(app_config)

migrate = Migrate(app, db)
manager = Manager(app)
# import models.user 

manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()



