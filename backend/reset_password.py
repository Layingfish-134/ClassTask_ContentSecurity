import sys
sys.path.insert(0, 'D:/rubbish for school/clss_content_sec/Task-6/backend')
from app.config.database_config import db
from app.models.user import User
from app import create_app
import bcrypt

app = create_app()
with app.app_context():
    student_id = '2023302181213'
    user = User.query.filter_by(username=student_id).first()
    
    if user:
        print(f'当前用户: {user.username}')
        print(f'当前密码哈希: {user.password_hash}')
        
        password = '123456'
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            print('当前密码已经是 123456')
        else:
            user.password_hash = hashed
            db.session.commit()
            print('密码已重置为 123456')
    else:
        print('用户不存在')