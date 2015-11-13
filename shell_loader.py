from app import app, User
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)
session = db.session
user = session.query(User).filter(User.first_name=='Russell').first()
