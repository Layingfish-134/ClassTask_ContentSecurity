import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'instance', 'attendance.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'connect_args': {'check_same_thread': False}
    }

    db.init_app(app)

    with app.app_context():
        from app.models import student, attendance_record, group_photo_record, user, emotion_record, group_photo_recognition_detail
        db.create_all()
        _ensure_sqlite_integer_primary_keys()


def _ensure_sqlite_integer_primary_keys():
    engine = db.engine
    if engine.dialect.name != 'sqlite':
        return

    tables = [
        ('emotion_record', 'emotion_id'),
        ('group_photo_recognition_detail', 'detail_id'),
        ('group_photo_record', 'photo_id'),
        ('attendance_record', 'record_id'),
    ]

    broken_tables = []
    with engine.connect() as conn:
        for table_name, pk_name in tables:
            columns = conn.exec_driver_sql(f"PRAGMA table_info({table_name})").fetchall()
            pk_column = next((column for column in columns if column[1] == pk_name), None)
            if pk_column and str(pk_column[2]).upper() != 'INTEGER':
                count = conn.exec_driver_sql(f"SELECT COUNT(*) FROM {table_name}").scalar()
                if count == 0:
                    broken_tables.append(table_name)

    if not broken_tables:
        return

    with engine.begin() as conn:
        conn.exec_driver_sql("PRAGMA foreign_keys=OFF")
        for table_name, _ in tables:
            if table_name in broken_tables:
                conn.exec_driver_sql(f"DROP TABLE IF EXISTS {table_name}")
        conn.exec_driver_sql("PRAGMA foreign_keys=ON")

    db.create_all()
