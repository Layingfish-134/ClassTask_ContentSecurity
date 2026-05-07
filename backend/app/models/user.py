from datetime import datetime
from app.config.database_config import db


class User(db.Model):
    __tablename__ = 'user_info'

    user_id = db.Column(db.String(20), primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('teacher', 'student', 'admin'), nullable=False)
    student_id = db.Column(db.String(20), db.ForeignKey('student_info.student_id', ondelete='RESTRICT'), nullable=True)
    status = db.Column(db.SmallInteger, nullable=False, default=1)
    token_version = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'role': self.role,
            'student_id': self.student_id,
            'status': self.status,
            'token_version': self.token_version,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
