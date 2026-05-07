from datetime import datetime
from app.config.database_config import db


class Student(db.Model):
    __tablename__ = 'student_info'

    student_id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    face_feature = db.Column(db.JSON, nullable=True)
    face_feature_hash = db.Column(db.String(64), nullable=True)
    feature_version = db.Column(db.Integer, nullable=False, default=1)
    feature_updated_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.SmallInteger, nullable=False, default=1)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    attendance_records = db.relationship('AttendanceRecord', backref='student', lazy='dynamic')
    user = db.relationship('User', backref='student_info', uselist=False)

    def to_dict(self):
        return {
            'student_id': self.student_id,
            'name': self.name,
            'class_name': self.class_name,
            'feature_version': self.feature_version,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
