from datetime import datetime
from app.services.face_recognition_service import FaceRecognitionService
from app.repositories.attendance_record_repository import AttendanceRecordRepository
from app.repositories.student_repository import StudentRepository
from app.models.attendance_record import AttendanceRecord
from app.models.emotion_record import EmotionRecord
from app.config.file_storage_config import get_upload_path
from app.config.database_config import db
from app.utils.image_utils import save_image
from app.dto.response.common import BizCode
import os
import base64


class AttendanceService:
    def __init__(self):
        self.face_service = FaceRecognitionService()

    def checkin(self, image_base64, image_format, idempotency_key=None,
                device_id=None, capture_time=None, frames_base64=None, current_user=None):
        if idempotency_key:
            existing = AttendanceRecord.query.filter_by(idempotency_key=idempotency_key).first()
            if existing:
                return existing.to_dict(), BizCode.CONFLICT

        liveness_result = None
        if frames_base64 and len(frames_base64) > 1:
            liveness_result = self.face_service.liveness_detector.detect_liveness_multi_frame_base64(frames_base64)
        else:
            liveness_result = self.face_service.liveness_detector.detect_liveness_from_base64(image_base64)

        if not liveness_result['is_live']:
            record = AttendanceRecord(
                student_id=None,
                status=0,
                liveness_passed=0,
                liveness_score=liveness_result['liveness_score'],
                spoof_type=liveness_result.get('spoof_type'),
                failure_reason=liveness_result.get('failure_reason', 'liveness_failed'),
                attendance_time=datetime.now(),
                idempotency_key=idempotency_key,
                device_id=device_id
            )
            db.session.add(record)
            db.session.commit()

            return {
                'status': 0,
                'liveness_passed': False,
                'liveness_score': liveness_result['liveness_score'],
                'spoof_type': liveness_result.get('spoof_type'),
                'failure_reason': liveness_result.get('failure_reason', 'liveness_failed')
            }, BizCode.PHOTO_ATTACK if liveness_result.get('spoof_type') == 'photo_attack' else BizCode.VIDEO_REPLAY if liveness_result.get('spoof_type') == 'video_replay' else BizCode.LIVENESS_FAILED

        target_student_id = None
        if current_user and current_user.role == 'student':
            target_student_id = current_user.student_id

        match_result, emotion_result = self.face_service.recognize_single_face(image_base64, target_student_id=target_student_id)

        image_path = None
        try:
            upload_dir = get_upload_path()
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
            filename = f"attendance_{timestamp}.{image_format}"
            filepath = os.path.join(upload_dir, filename)
            save_image(image_base64, filepath)
            image_path = filepath
        except Exception:
            pass

        if match_result.matched:
            student = StudentRepository.find_by_id(match_result.student_id)
            class_name = student.class_name if student else None

            record = AttendanceRecord(
                student_id=match_result.student_id,
                class_name=class_name,
                status=1,
                confidence=match_result.confidence,
                liveness_passed=1,
                liveness_score=liveness_result['liveness_score'],
                spoof_type=None,
                failure_reason=None,
                emotion=emotion_result.emotion,
                emotion_confidence=emotion_result.confidence,
                attendance_time=datetime.now(),
                image_path=image_path,
                idempotency_key=idempotency_key,
                device_id=device_id
            )
            db.session.add(record)
            db.session.flush()

            if emotion_result.emotion:
                emotion_record = EmotionRecord(
                    student_id=match_result.student_id,
                    class_name=class_name,
                    source_type='attendance',
                    attendance_record_id=record.record_id,
                    group_detail_id=None,
                    emotion=emotion_result.emotion,
                    confidence=emotion_result.confidence,
                    detected_at=datetime.now()
                )
                db.session.add(emotion_record)

            db.session.commit()

            return {
                'record_id': record.record_id,
                'student_id': match_result.student_id,
                'name': match_result.name,
                'class_name': class_name,
                'status': 1,
                'confidence': match_result.confidence,
                'liveness_passed': True,
                'liveness_score': liveness_result['liveness_score'],
                'spoof_type': None,
                'failure_reason': None,
                'emotion': emotion_result.emotion,
                'emotion_confidence': emotion_result.confidence,
                'attendance_time': record.attendance_time.isoformat(),
                'idempotency_key': idempotency_key
            }, BizCode.SUCCESS
        else:
            failure_reason = 'face_not_matched'
            record = AttendanceRecord(
                student_id=None,
                status=0,
                confidence=match_result.confidence,
                liveness_passed=1,
                liveness_score=liveness_result['liveness_score'],
                failure_reason=failure_reason,
                emotion=emotion_result.emotion,
                emotion_confidence=emotion_result.confidence,
                attendance_time=datetime.now(),
                image_path=image_path,
                idempotency_key=idempotency_key,
                device_id=device_id
            )
            db.session.add(record)
            db.session.commit()

            return {
                'status': 0,
                'liveness_passed': True,
                'liveness_score': liveness_result['liveness_score'],
                'failure_reason': failure_reason,
                'confidence': match_result.confidence
            }, BizCode.FACE_NOT_MATCHED

    def get_attendance_records(self, student_id=None, class_name=None,
                               start_time=None, end_time=None, status=None,
                               keyword=None, page=1, size=20, current_user=None):
        if current_user and current_user.role == 'student':
            student_id = current_user.student_id
            class_name = None

        records_pagination = AttendanceRecordRepository.find_all(
            student_id=student_id, class_name=class_name,
            start_time=start_time, end_time=end_time, status=status,
            keyword=keyword, page=page, size=size
        )
        return [r.to_dict() for r in records_pagination.items], records_pagination.total, page, size
