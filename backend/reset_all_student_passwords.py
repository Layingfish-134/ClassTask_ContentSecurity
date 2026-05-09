import sys
sys.path.insert(0, 'D:/rubbish for school/clss_content_sec/Task-6/backend')
from app.config.database_config import db
from app.models.user import User
from app import create_app
import bcrypt

app = create_app()
with app.app_context():
    students = User.query.filter_by(role='student').all()
    print(f'找到 {len(students)} 个学生用户')
    
    password = '123456'
    reset_count = 0
    
    for user in students:
        if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            user.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            reset_count += 1
    
    if reset_count > 0:
        db.session.commit()
        print(f'已重置 {reset_count} 个学生用户的密码为 123456')
    else:
        print('所有学生用户的密码已经是 123456')