from app import pgdb as db
from sqlalchemy.dialects.postgresql import JSON


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String())
    last_name = db.Column(db.String())
    email = db.Column(db.String())
    password_hash = db.Column.String()) 
    data = db.Column(JSON)

    def __init__(self, url, result_all, result_no_stop_words):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email 
        self.password_hash = password_hash 
        self.data = data 

    def __repr__(self):
        return '<id {}>'.format(self.id)