import argparse
import base64
import hashlib
import json
import os
import re
import sys
from datetime import datetime


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_ROOT = os.path.join(PROJECT_ROOT, 'backend')
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

import bcrypt  # noqa: E402
from app import create_app  # noqa: E402
from app.config.database_config import db  # noqa: E402
from app.models.student import Student  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.face_feature_extractor import FaceFeatureExtractor  # noqa: E402


IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png'}
DEFAULT_PASSWORD = '123456'


def parse_student_filename(filename):
    stem = os.path.splitext(filename)[0]
    parts = stem.split('-')
    if len(parts) < 3:
        return None

    student_id, name, class_name = parts[:3]
    if not re.fullmatch(r'\d{6,20}', student_id):
        return None

    return {
        'student_id': student_id,
        'name': name,
        'class_name': class_name,
    }


def image_file_to_base64(path):
    ext = os.path.splitext(path)[1].lower()
    mime = 'image/png' if ext == '.png' else 'image/jpeg'
    with open(path, 'rb') as file:
        return f"data:{mime};base64,{base64.b64encode(file.read()).decode('utf-8')}"


def feature_hash(feature_json):
    return hashlib.sha256(json.dumps(feature_json, ensure_ascii=False).encode('utf-8')).hexdigest()


def upsert_student_user(meta, feature):
    feature_json = feature.tolist() if feature is not None else None

    student = Student.query.get(meta['student_id'])
    if student is None:
        student = Student(student_id=meta['student_id'])
        db.session.add(student)

    student.name = meta['name']
    student.class_name = meta['class_name']
    student.status = 1
    if feature_json is not None:
        student.face_feature = feature_json
        student.face_feature_hash = feature_hash(feature_json)
        student.feature_version = (student.feature_version or 0) + 1
        student.feature_updated_at = datetime.now()

    user = User.query.filter_by(username=meta['student_id']).first()
    if user is None:
        user = User(
            user_id=f"u_student_{meta['student_id']}",
            username=meta['student_id'],
            role='student',
            student_id=meta['student_id'],
            status=1,
            password_hash=bcrypt.hashpw(DEFAULT_PASSWORD.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        )
        db.session.add(user)


def import_face_data(face_dir, limit=None):
    extractor = FaceFeatureExtractor()
    imported = 0
    skipped = []

    filenames = sorted(os.listdir(face_dir))
    if limit:
        filenames = filenames[:limit]

    for filename in filenames:
        path = os.path.join(face_dir, filename)
        if not os.path.isfile(path) or os.path.splitext(filename)[1].lower() not in IMAGE_EXTENSIONS:
            continue

        meta = parse_student_filename(filename)
        if not meta:
            skipped.append((filename, 'filename_parse_failed'))
            continue

        image_base64 = image_file_to_base64(path)
        feature = extractor.extract_feature_from_base64(image_base64)
        if feature is None:
            skipped.append((filename, 'face_feature_failed'))
            continue

        upsert_student_user(meta, feature)
        imported += 1
        print(f"imported {meta['student_id']} {meta['name']} {meta['class_name']}")

    db.session.commit()
    return imported, skipped


def main():
    parser = argparse.ArgumentParser(description='Import local face_data photos into the MySQL student table.')
    parser.add_argument('--face-dir', default=os.path.join(BACKEND_ROOT, 'uploads', 'face_data'))
    parser.add_argument('--limit', type=int, default=None)
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        imported, skipped = import_face_data(args.face_dir, args.limit)

    print(f"Imported students: {imported}")
    print(f"Skipped files: {len(skipped)}")
    for filename, reason in skipped[:20]:
        print(f"skipped {filename}: {reason}")


if __name__ == '__main__':
    main()
