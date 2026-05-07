from datetime import datetime
from app.config.database_config import db


class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_record'

    record_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    student_id = db.Column(db.String(20), db.ForeignKey('student_info.student_id', ondelete='SET NULL'), nullable=True)
    class_name = db.Column(db.String(50), nullable=True)
    status = db.Column(db.SmallInteger, nullable=False)
    confidence = db.Column(db.Numeric(5, 2), nullable=True)
    liveness_passed = db.Column(db.SmallInteger, nullable=False, default=0)
    liveness_score = db.Column(db.Numeric(5, 2), nullable=True)
    spoof_type = db.Column(db.String(30), nullable=True)
    failure_reason = db.Column(db.String(50), nullable=True)
    emotion = db.Column(db.String(20), nullable=True)
    emotion_confidence = db.Column(db.Numeric(5, 2), nullable=True)
    attendance_time = db.Column(db.DateTime, nullable=False)
    image_path = db.Column(db.String(255), nullable=True)
    request_id = db.Column(db.String(64), nullable=True)
    idempotency_key = db.Column(db.String(64), nullable=True, unique=True)
    device_id = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    emotion_records = db.relationship('EmotionRecord', backref='attendance_record', lazy='dynamic',
                                      foreign_keys='EmotionRecord.attendance_record_id')

    def to_dict(self):
        return {
            'record_id': self.record_id,
            'student_id': self.student_id,
            'name': self.student.name if self.student else None,
            'class_name': self.class_name or (self.student.class_name if self.student else None),
            'status': self.status,
            'confidence': float(self.confidence) if self.confidence else None,
            'liveness_passed': bool(self.liveness_passed),
            'liveness_score': float(self.liveness_score) if self.liveness_score else None,
            'spoof_type': self.spoof_type,
            'failure_reason': self.failure_reason,
            'emotion': self.emotion,
            'emotion_confidence': float(self.emotion_confidence) if self.emotion_confidence else None,
            'attendance_time': self.attendance_time.isoformat() if self.attendance_time else None,
            'idempotency_key': self.idempotency_key
        }
