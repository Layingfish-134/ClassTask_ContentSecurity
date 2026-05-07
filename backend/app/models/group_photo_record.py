from datetime import datetime
from app.config.database_config import db


class GroupPhotoRecord(db.Model):
    __tablename__ = 'group_photo_record'

    photo_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    photo_name = db.Column(db.String(255), nullable=False)
    photo_path = db.Column(db.String(255), nullable=False)
    activity_name = db.Column(db.String(100), nullable=True)
    activity_time = db.Column(db.DateTime, nullable=True)
    total_faces = db.Column(db.Integer, nullable=False, default=0)
    recognized_count = db.Column(db.Integer, nullable=False, default=0)
    unrecognized_count = db.Column(db.Integer, nullable=False, default=0)
    created_by = db.Column(db.String(20), db.ForeignKey('user_info.user_id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    details = db.relationship('GroupPhotoRecognitionDetail', backref='photo', lazy='dynamic',
                              cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'photo_id': self.photo_id,
            'photo_name': self.photo_name,
            'activity_name': self.activity_name,
            'activity_time': self.activity_time.isoformat() if self.activity_time else None,
            'total_faces': self.total_faces,
            'recognized_count': self.recognized_count,
            'unrecognized_count': self.unrecognized_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
