from app.config.database_config import db
from app.models.student import Student


class StudentRepository:
    @staticmethod
    def find_by_id(student_id):
        return Student.query.get(student_id)

    @staticmethod
    def find_all(page=1, size=20, class_name=None, keyword=None):
        query = Student.query.filter(Student.status == 1)
        if class_name:
            query = query.filter(Student.class_name == class_name)
        if keyword:
            query = query.filter(
                db.or_(
                    Student.student_id.contains(keyword),
                    Student.name.contains(keyword)
                )
            )
        return query.paginate(page=page, per_page=size, error_out=False)

    @staticmethod
    def find_all_with_features():
        return Student.query.filter(Student.face_feature.isnot(None), Student.status == 1).all()

    @staticmethod
    def save(student):
        db.session.add(student)
        db.session.commit()
        return student

    @staticmethod
    def update(student):
        db.session.commit()
        return student

    @staticmethod
    def delete(student):
        student.status = 0
        db.session.commit()

    @staticmethod
    def count_by_class(class_name):
        return Student.query.filter(Student.class_name == class_name, Student.status == 1).count()

    @staticmethod
    def find_all_cursor(cursor=None, size=20, class_name=None, keyword=None):
        query = Student.query.filter(Student.status == 1)
        if class_name:
            query = query.filter(Student.class_name == class_name)
        if keyword:
            query = query.filter(
                db.or_(
                    Student.student_id.contains(keyword),
                    Student.name.contains(keyword)
                )
            )
        query = query.order_by(Student.student_id.asc())
        if cursor:
            query = query.filter(Student.student_id > cursor)
        records = query.limit(size + 1).all()
        has_more = len(records) > size
        records = records[:size]
        next_cursor = records[-1].student_id if records and has_more else None
        return records, has_more, next_cursor
