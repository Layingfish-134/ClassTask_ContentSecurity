from datetime import datetime
from app.config.database_config import db


class EmotionRecord(db.Model):
    __tablename__ = 'emotion_record'

    emotion_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.String(20), db.ForeignKey('student_info.student_id', ondelete='SET NULL'), nullable=True)
    class_name = db.Column(db.String(50), nullable=True)
    source_type = db.Column(db.Enum('attendance', 'group_photo'), nullable=False)
    attendance_record_id = db.Column(db.Integer, db.ForeignKey('attendance_record.record_id', ondelete='CASCADE'), nullable=True)
    group_detail_id = db.Column(db.Integer, db.ForeignKey('group_photo_recognition_detail.detail_id', ondelete='CASCADE'), nullable=True)
    emotion = db.Column(db.String(20), nullable=False)
    confidence = db.Column(db.Numeric(5, 2), nullable=True)
    detected_at = db.Column(db.DateTime, nullable=False)
    face_box = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def to_dict(self):
        return {
            'emotion_id': self.emotion_id,
            'student_id': self.student_id,
            'class_name': self.class_name,
            'source_type': self.source_type,
            'emotion': self.emotion,
            'confidence': float(self.confidence) if self.confidence else None,
            'detected_at': self.detected_at.isoformat() if self.detected_at else None
        }
