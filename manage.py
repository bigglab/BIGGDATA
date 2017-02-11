
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand

from app import app, db
from models import * 


app.config.from_pyfile('config.py')

migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)



if __name__ == '__main__':
    manager.run()




