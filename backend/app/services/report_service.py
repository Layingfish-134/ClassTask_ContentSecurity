import json
from datetime import datetime
from app.services.face_recognition_service import FaceRecognitionService
from app.repositories.group_photo_record_repository import GroupPhotoRecordRepository, GroupPhotoRecognitionDetailRepository
from app.repositories.attendance_record_repository import AttendanceRecordRepository
from app.models.group_photo_record import GroupPhotoRecord
from app.models.group_photo_recognition_detail import GroupPhotoRecognitionDetail
from app.models.emotion_record import EmotionRecord
from app.config.file_storage_config import get_upload_path
from app.config.database_config import db
from app.utils.image_utils import save_image
import os


class ReportService:
    def __init__(self):
        self.face_service = FaceRecognitionService()

    def process_group_photo(self, photo_base64, image_format, photo_name='',
                            activity_name='', activity_time=None, created_by=None):
        results = self.face_service.recognize_multiple_faces(photo_base64)

        recognized_count = 0
        unrecognized_count = 0
        details = []
        emotion_records = []

        for result in results:
            match = result['match']
            emotion = result['emotion']

            if match.matched:
                recognized_count += 1
                detail = GroupPhotoRecognitionDetail(
                    student_id=match.student_id,
                    class_name=match.class_name,
                    status=1,
                    confidence=match.confidence,
                    face_box=result.get('box'),
                    emotion=emotion.emotion,
                    emotion_confidence=emotion.confidence
                )
                if emotion.emotion:
                    er = EmotionRecord(
                        student_id=match.student_id,
                        class_name=match.class_name,
                        source_type='group_photo',
                        emotion=emotion.emotion,
                        confidence=emotion.confidence,
                        detected_at=datetime.now(),
                        face_box=result.get('box')
                    )
                    emotion_records.append(er)
            else:
                unrecognized_count += 1
                detail = GroupPhotoRecognitionDetail(
                    student_id=None,
                    status=0,
                    confidence=match.confidence if match else 0,
                    face_box=result.get('box'),
                    emotion=emotion.emotion,
                    emotion_confidence=emotion.confidence,
                    failure_reason='face_not_matched'
                )

            details.append(detail)

        photo_path = None
        try:
            upload_dir = get_upload_path()
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
            filename = f"group_photo_{timestamp}.{image_format}"
            filepath = os.path.join(upload_dir, filename)
            save_image(photo_base64, filepath)
            photo_path = filepath
        except Exception:
            pass

        if not photo_name:
            photo_name = f"group_photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{image_format}"

        act_time = None
        if activity_time:
            try:
                act_time = datetime.fromisoformat(activity_time)
            except (ValueError, TypeError):
                act_time = None

        record = GroupPhotoRecord(
            photo_name=photo_name,
            photo_path=photo_path or '',
            activity_name=activity_name,
            activity_time=act_time,
            total_faces=len(results),
            recognized_count=recognized_count,
            unrecognized_count=unrecognized_count,
            created_by=created_by
        )
        db.session.add(record)
        db.session.flush()

        for detail in details:
            detail.photo_id = record.photo_id
            db.session.add(detail)
        db.session.flush()

        for er in emotion_records:
            er.group_detail_id = details[0].detail_id if details else None
            for d in details:
                if d.student_id == er.student_id:
                    er.group_detail_id = d.detail_id
                    break
            db.session.add(er)

        db.session.commit()

        student_list = []
        for d in details:
            if d.status == 1:
                student_list.append({
                    'student_id': d.student_id,
                    'name': d.student.name if d.student else '',
                    'class_name': d.class_name,
                    'confidence': float(d.confidence) if d.confidence else None,
                    'emotion': d.emotion,
                    'emotion_confidence': float(d.emotion_confidence) if d.emotion_confidence else None
                })

        return {
            'photo_id': record.photo_id,
            'photo_name': photo_name,
            'activity_name': activity_name,
            'recognized_count': recognized_count,
            'total_faces': len(results),
            'unrecognized_count': unrecognized_count,
            'students': student_list
        }

    def get_group_photo_records(self, activity_name=None, class_name=None,
                                start_time=None, end_time=None,
                                cursor=None, size=20):
        records, has_more, next_cursor = GroupPhotoRecordRepository.find_all_cursor(
            cursor=cursor, size=size,
            activity_name=activity_name, class_name=class_name,
            start_time=start_time, end_time=end_time
        )
        result_list = []
        for record in records:
            d = record.to_dict()
            d['students'] = [detail.to_dict() for detail in record.details.all()]
            result_list.append(d)
        return result_list, size, next_cursor, has_more

    def get_emotion_statistics(self, class_name=None, student_id=None,
                               source_type=None, start_time=None, end_time=None):
        return AttendanceRecordRepository.find_emotion_statistics(
            class_name=class_name, student_id=student_id,
            source_type=source_type, start_time=start_time, end_time=end_time
        )

    def get_emotion_trend(self, class_name=None, student_id=None,
                          source_type=None, start_time=None, end_time=None):
        return AttendanceRecordRepository.find_emotion_trend(
            class_name=class_name, student_id=student_id,
            source_type=source_type, start_time=start_time, end_time=end_time
        )

    def export_attendance_report(self, class_name=None, start_time=None, end_time=None):
        import pandas as pd
        from io import BytesIO

        records = AttendanceRecordRepository.find_by_date_range(
            start_time=start_time, end_time=end_time, class_name=class_name
        )

        data = []
        for record in records:
            data.append({
                '记录ID': record.record_id,
                '学号': record.student_id or '',
                '姓名': record.student.name if record.student else '',
                '班级': record.class_name or '',
                '考勤状态': '成功' if record.status == 1 else '失败',
                '匹配置信度': float(record.confidence) if record.confidence else '',
                '活体检测': '通过' if record.liveness_passed else '未通过',
                '活体分数': float(record.liveness_score) if record.liveness_score else '',
                '攻击类型': record.spoof_type or '',
                '失败原因': record.failure_reason or '',
                '情绪类型': record.emotion or '',
                '情绪置信度': float(record.emotion_confidence) if record.emotion_confidence else '',
                '考勤时间': record.attendance_time.strftime('%Y-%m-%d %H:%M:%S') if record.attendance_time else ''
            })

        df = pd.DataFrame(data)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='考勤记录')
        output.seek(0)
        return output.getvalue()

    def export_activity_frequency_report(self, class_name=None):
        import pandas as pd
        from io import BytesIO

        frequency = GroupPhotoRecordRepository.get_activity_frequency(class_name=class_name)

        data = []
        for item in frequency:
            data.append({
                '学号': item['student_id'],
                '姓名': item['name'],
                '班级': item['class_name'],
                '参与活动次数': item['count']
            })

        df = pd.DataFrame(data)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='活动参与频次')
        output.seek(0)
        return output.getvalue()
