from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    original_content = db.Column(db.Text, nullable=False)
    rephrased_content = db.Column(db.Text, nullable=True)
    sentiment_analysis_result = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    consent_to_store = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Message {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'original_content': self.original_content,
            'rephrased_content': self.rephrased_content,
            'sentiment_analysis_result': self.sentiment_analysis_result,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'consent_to_store': self.consent_to_store
        }

