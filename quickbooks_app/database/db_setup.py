from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy

class User(db.Model):
    id = db.Column(db.Inter)