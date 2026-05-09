import sys
sys.path.insert(0, 'D:/rubbish for school/clss_content_sec/Task-6/backend')
from app.config.database_config import db
from app.models.student import Student
from app.models.user import User
from app import create_app

app = create_app()
with app.app_context():
    print('=== 所有学生记录 ===')
    students = Student.query.all()
    for s in students:
        print(f'{s.student_id} - {s.name} - {s.class_name}')
    
    print()
    print('=== 所有用户记录 ===')
    users = User.query.all()
    for u in users:
        print(f'{u.username} - {u.role} - 学号: {u.student_id}')
    
    print()
    print('=== 学号 2023302181213 查询 ===')
    student = Student.query.filter_by(student_id='2023302181213').first()
    user = User.query.filter_by(username='2023302181213').first() or User.query.filter_by(student_id='2023302181213').first()
    
    if student:
        print(f'学生存在: {student.name}')
    else:
        print('学生不存在')
    
    if user:
        print(f'用户存在: {user.username}, 角色: {user.role}')
    else:
        print('用户不存在')