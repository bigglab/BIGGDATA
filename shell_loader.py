from app import *
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)
session = db.session
user = session.query(User).filter(User.first_name=='Russell').first()
# f = db.session.query(File).all()[0]
q = db.session.query 
a = db.session.add 
c = db.session.commit 