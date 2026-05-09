import json
import hashlib
from app.repositories.student_repository import StudentRepository
from app.models.student import Student
from app.models.user import User
from app.services.face_feature_extractor import FaceFeatureExtractor
from app.config.database_config import db
import bcrypt


class StudentService:
    def __init__(self):
        self.feature_extractor = FaceFeatureExtractor()

    def create_student(self, student_id, name, class_name, face_image_base64,
                       image_format='jpg', username=None, password=None):
        existing = StudentRepository.find_by_id(student_id)
        if existing:
            raise ValueError(f'学号 {student_id} 已存在')

        feature = self.feature_extractor.extract_feature_from_base64(face_image_base64)
        feature_json = feature.tolist() if feature is not None else None
        feature_hash = None
        if feature is not None:
            feature_hash = hashlib.sha256(json.dumps(feature_json).encode()).hexdigest()

        student = Student(
            student_id=student_id,
            name=name,
            class_name=class_name,
            face_feature=feature_json,
            face_feature_hash=feature_hash,
            feature_version=1,
            feature_updated_at=db.func.now() if feature is not None else None,
            status=1
        )
        db.session.add(student)

        user_username = username if username else student_id
        user_password = password if password else '123456'
        
        existing_user = User.query.filter_by(username=user_username).first()
        if existing_user:
            raise ValueError(f'用户名 {user_username} 已存在')
        hashed = bcrypt.hashpw(user_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = User(
            user_id=f"stu_{student_id}",
            username=user_username,
            password_hash=hashed,
            role='student',
            student_id=student_id,
            status=1
        )
        db.session.add(user)

        db.session.commit()
        return student

    def update_student(self, student_id, name=None, class_name=None, face_image_base64=None,
                       image_format='jpg'):
        student = StudentRepository.find_by_id(student_id)
        if not student:
            raise ValueError(f'学号 {student_id} 不存在')

        if name is not None:
            student.name = name
        if class_name is not None:
            student.class_name = class_name
        if face_image_base64 is not None:
            feature = self.feature_extractor.extract_feature_from_base64(face_image_base64)
            student.face_feature = feature.tolist() if feature is not None else None
            if feature is not None:
                student.face_feature_hash = hashlib.sha256(
                    json.dumps(student.face_feature).encode()
                ).hexdigest()
                student.feature_version = (student.feature_version or 0) + 1
                student.feature_updated_at = db.func.now()

        db.session.commit()
        return student

    def delete_student(self, student_id):
        student = StudentRepository.find_by_id(student_id)
        if not student:
            raise ValueError(f'学号 {student_id} 不存在')
        student.status = 0
        db.session.commit()

    def get_students(self, class_name=None, keyword=None, page=1, size=20):
        pagination = StudentRepository.find_all(
            page=page, size=size,
            class_name=class_name, keyword=keyword
        )
        return [s.to_dict() for s in pagination.items], pagination.total

    def get_student_by_id(self, student_id):
        return StudentRepository.find_by_id(student_id)

    def batch_import(self, students_data):
        success_count = 0
        fail_count = 0
        errors = []

        for idx, item in enumerate(students_data):
            try:
                student_id = item.get('student_id')
                name = item.get('name')
                class_name = item.get('class_name')
                face_image_base64 = item.get('face_image_base64')

                if not all([student_id, name, class_name, face_image_base64]):
                    fail_count += 1
                    errors.append({'index': idx, 'student_id': student_id, 'reason': 'missing_field'})
                    continue

                existing = StudentRepository.find_by_id(student_id)
                if existing:
                    fail_count += 1
                    errors.append({'index': idx, 'student_id': student_id, 'reason': 'duplicate'})
                    continue

                self.create_student(
                    student_id=student_id,
                    name=name,
                    class_name=class_name,
                    face_image_base64=face_image_base64,
                    username=item.get('username'),
                    password=item.get('password', '123456')
                )
                success_count += 1
            except Exception as e:
                fail_count += 1
                errors.append({'index': idx, 'student_id': item.get('student_id', ''), 'reason': str(e)})

        return {
            'total': len(students_data),
            'success_count': success_count,
            'fail_count': fail_count,
            'errors': errors
        }
