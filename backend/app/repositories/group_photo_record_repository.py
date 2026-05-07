from datetime import datetime
from app.config.database_config import db
from app.models.group_photo_record import GroupPhotoRecord
from app.models.group_photo_recognition_detail import GroupPhotoRecognitionDetail


class GroupPhotoRecordRepository:
    @staticmethod
    def save(record):
        db.session.add(record)
        db.session.commit()
        return record

    @staticmethod
    def find_by_id(photo_id):
        return GroupPhotoRecord.query.get(photo_id)

    @staticmethod
    def find_all(page=1, size=20, activity_name=None, start_time=None, end_time=None):
        query = GroupPhotoRecord.query

        if activity_name:
            query = query.filter(GroupPhotoRecord.activity_name.contains(activity_name))
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time)
                query = query.filter(GroupPhotoRecord.created_at >= start_dt)
            except (ValueError, TypeError):
                pass
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time)
                query = query.filter(GroupPhotoRecord.created_at <= end_dt)
            except (ValueError, TypeError):
                pass

        query = query.order_by(GroupPhotoRecord.created_at.desc())
        return query.paginate(page=page, per_page=size, error_out=False)

    @staticmethod
    def find_all_cursor(cursor=None, size=20, activity_name=None,
                        class_name=None, start_time=None, end_time=None):
        query = GroupPhotoRecord.query

        if activity_name:
            query = query.filter(GroupPhotoRecord.activity_name.contains(activity_name))
        if class_name:
            query = query.filter(
                GroupPhotoRecord.details.any(GroupPhotoRecognitionDetail.class_name == class_name)
            )
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time)
                query = query.filter(GroupPhotoRecord.created_at >= start_dt)
            except (ValueError, TypeError):
                pass
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time)
                query = query.filter(GroupPhotoRecord.created_at <= end_dt)
            except (ValueError, TypeError):
                pass

        query = query.order_by(GroupPhotoRecord.photo_id.desc())
        if cursor:
            try:
                cursor_id = int(cursor)
                query = query.filter(GroupPhotoRecord.photo_id < cursor_id)
            except (ValueError, TypeError):
                pass

        records = query.limit(size + 1).all()
        has_more = len(records) > size
        records = records[:size]
        next_cursor = str(records[-1].photo_id) if records and has_more else None
        return records, has_more, next_cursor

    @staticmethod
    def get_activity_frequency(class_name=None):
        query = db.session.query(
            GroupPhotoRecognitionDetail.student_id,
            GroupPhotoRecognitionDetail.class_name,
            db.func.count(GroupPhotoRecognitionDetail.detail_id).label('count')
        ).filter(
            GroupPhotoRecognitionDetail.status == 1,
            GroupPhotoRecognitionDetail.student_id.isnot(None)
        )

        if class_name:
            query = query.filter(GroupPhotoRecognitionDetail.class_name == class_name)

        query = query.group_by(
            GroupPhotoRecognitionDetail.student_id,
            GroupPhotoRecognitionDetail.class_name
        )

        results = query.all()

        frequency = []
        for student_id, sclass, count in results:
            from app.models.student import Student
            student = Student.query.get(student_id)
            frequency.append({
                'student_id': student_id,
                'name': student.name if student else '',
                'class_name': sclass,
                'count': count
            })

        return sorted(frequency, key=lambda x: x['count'], reverse=True)


class GroupPhotoRecognitionDetailRepository:
    @staticmethod
    def save(detail):
        db.session.add(detail)
        db.session.commit()
        return detail

    @staticmethod
    def save_batch(details):
        db.session.add_all(details)
        db.session.commit()
        return details

    @staticmethod
    def find_by_photo_id(photo_id):
        return GroupPhotoRecognitionDetail.query.filter_by(photo_id=photo_id).all()
