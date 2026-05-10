import json
import hashlib
import base64
import os
import re
import zipfile
from app.repositories.student_repository import StudentRepository
from app.models.student import Student
from app.models.user import User
from app.services.face_feature_extractor import FaceFeatureExtractor
from app.config.database_config import db
import bcrypt


class StudentService:
    ZIP_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.jepg', '.png'}

    def __init__(self):
        self.feature_extractor = FaceFeatureExtractor()

    def create_student(self, student_id, name, class_name, face_image_base64,
                       image_format='jpg', username=None, password=None):
        feature = self.feature_extractor.extract_feature_from_base64(face_image_base64)
        if feature is None:
            raise ValueError('未检测到有效人脸，请检查照片是否清晰')

        return self._create_student_with_feature(
            student_id=student_id,
            name=name,
            class_name=class_name,
            feature=feature,
            username=username,
            password=password
        )

    def _create_student_with_feature(self, student_id, name, class_name, feature,
                                     username=None, password=None):
        existing = StudentRepository.find_by_id(student_id)
        if existing and existing.status == 1:
            raise ValueError(f'学号 {student_id} 已存在')

        feature_json = feature.tolist() if feature is not None else None
        feature_hash = None
        if feature is not None:
            feature_hash = hashlib.sha256(json.dumps(feature_json).encode()).hexdigest()

        if existing:
            student = existing
            student.name = name
            student.class_name = class_name
            student.face_feature = feature_json
            student.face_feature_hash = feature_hash
            student.feature_version = (student.feature_version or 0) + 1
            student.feature_updated_at = db.func.now() if feature is not None else None
            student.status = 1
        else:
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
        if existing_user and existing_user.student_id != student_id:
            raise ValueError(f'用户名 {user_username} 已存在')

        if existing_user:
            existing_user.role = 'student'
            existing_user.student_id = student_id
            existing_user.status = 1
        else:
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
        if student.user:
            student.user.status = 0
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
                if existing and existing.status == 1:
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

    def batch_import_photo_zip(self, zip_file):
        success_count = 0
        fail_count = 0
        errors = []
        total = 0

        try:
            archive = zipfile.ZipFile(zip_file)
        except zipfile.BadZipFile:
            raise ValueError('压缩包格式错误，请上传有效的 zip 文件')

        with archive:
            entries = [
                item for item in archive.infolist()
                if not item.is_dir() and not self._is_system_zip_entry(item.filename)
            ]

            if not entries:
                raise ValueError('压缩包内未找到学生照片')

            for item in entries:
                filename = os.path.basename(item.filename)
                if not filename:
                    continue

                total += 1
                if os.path.splitext(filename)[1].lower() not in self.ZIP_IMAGE_EXTENSIONS:
                    fail_count += 1
                    errors.append({'filename': filename, 'reason': '仅支持 jpg、jpeg、png 格式照片'})
                    continue

                meta = self._parse_student_photo_filename(filename)
                if not meta:
                    fail_count += 1
                    errors.append({
                        'filename': filename,
                        'reason': '文件名格式错误，应为 学号-姓名-专业-性别.jpg/jpeg/png'
                    })
                    continue

                existing = StudentRepository.find_by_id(meta['student_id'])
                if existing and existing.status == 1:
                    fail_count += 1
                    errors.append({
                        'filename': filename,
                        'student_id': meta['student_id'],
                        'reason': '学号已存在'
                    })
                    continue

                try:
                    image_bytes = archive.read(item)
                    image_base64 = self._image_bytes_to_base64(image_bytes, filename)
                    feature = self.feature_extractor.extract_feature_from_base64(image_base64)
                    if feature is None:
                        raise ValueError('未检测到有效人脸，请检查照片是否清晰')

                    self._create_student_with_feature(
                        student_id=meta['student_id'],
                        name=meta['name'],
                        class_name=meta['class_name'],
                        feature=feature,
                        password='123456'
                    )
                    success_count += 1
                except Exception as e:
                    fail_count += 1
                    db.session.rollback()
                    errors.append({
                        'filename': filename,
                        'student_id': meta.get('student_id'),
                        'reason': str(e)
                    })

        return {
            'total': total,
            'success_count': success_count,
            'fail_count': fail_count,
            'errors': errors
        }

    def _parse_student_photo_filename(self, filename):
        stem, ext = os.path.splitext(filename)
        if ext.lower() not in self.ZIP_IMAGE_EXTENSIONS:
            return None

        parts = stem.split('-')
        if len(parts) != 4:
            return None

        student_id, name, class_name, gender = [part.strip() for part in parts]
        if not re.fullmatch(r'\d{6,20}', student_id):
            return None
        if not name or not class_name or not gender:
            return None

        return {
            'student_id': student_id,
            'name': name,
            'class_name': class_name
        }

    def _image_bytes_to_base64(self, image_bytes, filename):
        ext = os.path.splitext(filename)[1].lower()
        mime = 'image/png' if ext == '.png' else 'image/jpeg'
        encoded = base64.b64encode(image_bytes).decode('utf-8')
        return f'data:{mime};base64,{encoded}'

    def _is_system_zip_entry(self, filename):
        normalized = filename.replace('\\', '/')
        return normalized.startswith('__MACOSX/') or os.path.basename(normalized).startswith('.')
