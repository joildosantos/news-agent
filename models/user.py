from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    api_key_news = db.Column(db.String(255), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Relacionamentos
    topics = db.relationship('Topic', backref='user', lazy=True, cascade='all, delete-orphan')
    sources = db.relationship('Source', backref='user', lazy=True, cascade='all, delete-orphan')
    recipients = db.relationship('Recipient', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'api_key_news': self.api_key_news,
            'is_admin': self.is_admin
        }

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic_name = db.Column(db.String(100), nullable=False)
    priority = db.Column(db.Integer, default=3)  # 1-5, 1=mais importante
    avoid = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'topic_name': self.topic_name,
            'priority': self.priority,
            'avoid': self.avoid
        }

class Source(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    source_name = db.Column(db.String(200), nullable=False)
    priority = db.Column(db.Integer, default=3)  # 1-5, 1=mais importante
    avoid = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'source_name': self.source_name,
            'priority': self.priority,
            'avoid': self.avoid
        }

class Recipient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'whatsapp' ou 'email'
    address = db.Column(db.String(200), nullable=False)  # número ou email
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'address': self.address
        }
