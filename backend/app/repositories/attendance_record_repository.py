from datetime import datetime
from app.config.database_config import db
from app.models.attendance_record import AttendanceRecord


class AttendanceRecordRepository:
    @staticmethod
    def save(record):
        db.session.add(record)
        db.session.commit()
        return record

    @staticmethod
    def find_by_id(record_id):
        return AttendanceRecord.query.get(record_id)

    @staticmethod
    def find_all(page=1, size=20, student_id=None, class_name=None,
                 start_time=None, end_time=None, status=None):
        query = AttendanceRecord.query.join(
            AttendanceRecord.student, isouter=True
        )

        if student_id:
            query = query.filter(AttendanceRecord.student_id == student_id)
        if class_name:
            query = query.filter(AttendanceRecord.class_name == class_name)
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time)
                query = query.filter(AttendanceRecord.attendance_time >= start_dt)
            except (ValueError, TypeError):
                pass
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time)
                query = query.filter(AttendanceRecord.attendance_time <= end_dt)
            except (ValueError, TypeError):
                pass
        if status is not None:
            query = query.filter(AttendanceRecord.status == status)

        query = query.order_by(AttendanceRecord.attendance_time.desc())
        return query.paginate(page=page, per_page=size, error_out=False)

    @staticmethod
    def find_all_cursor(cursor=None, size=20, student_id=None, class_name=None,
                        start_time=None, end_time=None, status=None):
        query = AttendanceRecord.query

        if student_id:
            query = query.filter(AttendanceRecord.student_id == student_id)
        if class_name:
            query = query.filter(AttendanceRecord.class_name == class_name)
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time)
                query = query.filter(AttendanceRecord.attendance_time >= start_dt)
            except (ValueError, TypeError):
                pass
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time)
                query = query.filter(AttendanceRecord.attendance_time <= end_dt)
            except (ValueError, TypeError):
                pass
        if status is not None:
            query = query.filter(AttendanceRecord.status == status)

        query = query.order_by(AttendanceRecord.record_id.desc())
        if cursor:
            try:
                cursor_id = int(cursor)
                query = query.filter(AttendanceRecord.record_id < cursor_id)
            except (ValueError, TypeError):
                pass

        records = query.limit(size + 1).all()
        has_more = len(records) > size
        records = records[:size]
        next_cursor = str(records[-1].record_id) if records and has_more else None
        total = len(records)
        return records, total, has_more, next_cursor

    @staticmethod
    def find_emotion_statistics(class_name=None, student_id=None,
                                source_type=None, start_time=None, end_time=None):
        from app.models.emotion_record import EmotionRecord
        query = db.session.query(
            EmotionRecord.emotion,
            db.func.count(EmotionRecord.emotion_id)
        )

        if class_name:
            query = query.filter(EmotionRecord.class_name == class_name)
        if student_id:
            query = query.filter(EmotionRecord.student_id == student_id)
        if source_type:
            query = query.filter(EmotionRecord.source_type == source_type)
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time)
                query = query.filter(EmotionRecord.detected_at >= start_dt)
            except (ValueError, TypeError):
                pass
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time)
                query = query.filter(EmotionRecord.detected_at <= end_dt)
            except (ValueError, TypeError):
                pass

        query = query.filter(EmotionRecord.emotion.isnot(None))
        results = query.group_by(EmotionRecord.emotion).all()

        distribution = {}
        total = 0
        for emotion, count in results:
            distribution[emotion] = count
            total += count

        return {'total_count': total, 'distribution': distribution}

    @staticmethod
    def find_by_date_range(start_time, end_time, class_name=None):
        query = AttendanceRecord.query
        if class_name:
            query = query.filter(AttendanceRecord.class_name == class_name)
        try:
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
            query = query.filter(
                AttendanceRecord.attendance_time.between(start_dt, end_dt)
            )
        except (ValueError, TypeError):
            pass
        return query.all()
