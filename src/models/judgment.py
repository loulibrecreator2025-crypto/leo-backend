from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Judgment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    document_path = db.Column(db.String(255), nullable=False)
    extracted_data_json = db.Column(db.JSON, nullable=True)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Judgment {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'document_path': self.document_path,
            'extracted_data_json': self.extracted_data_json,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None
        }

