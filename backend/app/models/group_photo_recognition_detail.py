from datetime import datetime
from app.config.database_config import db


class GroupPhotoRecognitionDetail(db.Model):
    __tablename__ = 'group_photo_recognition_detail'

    detail_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    photo_id = db.Column(db.BigInteger, db.ForeignKey('group_photo_record.photo_id', ondelete='CASCADE'), nullable=False)
    student_id = db.Column(db.String(20), db.ForeignKey('student_info.student_id', ondelete='SET NULL'), nullable=True)
    class_name = db.Column(db.String(50), nullable=True)
    status = db.Column(db.SmallInteger, nullable=False)
    confidence = db.Column(db.Numeric(5, 2), nullable=True)
    face_box = db.Column(db.JSON, nullable=True)
    emotion = db.Column(db.String(20), nullable=True)
    emotion_confidence = db.Column(db.Numeric(5, 2), nullable=True)
    failure_reason = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    emotion_records = db.relationship('EmotionRecord', backref='group_detail', lazy='dynamic',
                                      foreign_keys='EmotionRecord.group_detail_id')

    def to_dict(self):
        return {
            'detail_id': self.detail_id,
            'photo_id': self.photo_id,
            'student_id': self.student_id,
            'name': self.student.name if self.student else None,
            'class_name': self.class_name,
            'status': self.status,
            'confidence': float(self.confidence) if self.confidence else None,
            'face_box': self.face_box,
            'emotion': self.emotion,
            'emotion_confidence': float(self.emotion_confidence) if self.emotion_confidence else None,
            'failure_reason': self.failure_reason
        }
