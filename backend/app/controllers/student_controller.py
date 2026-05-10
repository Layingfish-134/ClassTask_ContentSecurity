from flask_restful import Resource
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.student_service import StudentService
from app.dto.request.parsers import student_create_parser, student_query_parser, student_update_parser
from app.dto.response.common import success_response, error_response, paginated_response, BizCode
from app.utils.permission import require_teacher_or_admin, get_current_user, enforce_student_data_access
import pandas as pd
import io


class StudentListResource(Resource):
    def __init__(self):
        self.student_service = StudentService()

    @jwt_required()
    def get(self):
        args = student_query_parser.parse_args()
        current_user = get_current_user()
        if not current_user:
            return error_response('未登录', BizCode.UNAUTHORIZED)

        if current_user.role == 'student':
            return error_response('学生账号无权进入学生管理', BizCode.FORBIDDEN)

        class_name = args.get('class_name')

        try:
            page = args.get('page', 1)
            size = args.get('size', 20)
            students, total = self.student_service.get_students(
                class_name=class_name,
                keyword=args.get('keyword'),
                page=page,
                size=size
            )
            return {
                'code': 200,
                'message': 'success',
                'data': {
                    'records': students,
                    'total': total,
                    'page': page,
                    'size': size
                }
            }
        except Exception as e:
            return error_response(f'查询学生列表异常: {str(e)}', BizCode.INTERNAL_ERROR)

    @jwt_required()
    def post(self):
        current_user = get_current_user()
        if not current_user or current_user.role not in ('teacher', 'admin'):
            return error_response('无权限执行此操作', BizCode.FORBIDDEN)

        args = student_create_parser.parse_args()
        try:
            student = self.student_service.create_student(
                student_id=args['student_id'],
                name=args['name'],
                class_name=args['class_name'],
                face_image_base64=args['face_image_base64'],
                image_format=args.get('image_format', 'jpg'),
                username=args.get('username'),
                password=args.get('password')
            )
            return success_response(student.to_dict(), '学生创建成功', 201)
        except ValueError as e:
            return error_response(str(e), BizCode.CONFLICT)
        except Exception as e:
            return error_response(f'创建学生异常: {str(e)}', BizCode.INTERNAL_ERROR)


class StudentDetailResource(Resource):
    def __init__(self):
        self.student_service = StudentService()

    @jwt_required()
    def get(self, student_id):
        current_user = get_current_user()
        if not current_user:
            return error_response('未登录', BizCode.UNAUTHORIZED)
        if current_user.role == 'student':
            return error_response('学生账号无权进入学生管理', BizCode.FORBIDDEN)

        student = self.student_service.get_student_by_id(student_id)
        if not student:
            return error_response(f'学号 {student_id} 不存在', BizCode.NOT_FOUND)
        return success_response(student.to_dict())

    @jwt_required()
    def put(self, student_id):
        current_user = get_current_user()
        if not current_user or current_user.role not in ('teacher', 'admin'):
            return error_response('无权限执行此操作', BizCode.FORBIDDEN)

        args = student_update_parser.parse_args()
        try:
            student = self.student_service.update_student(
                student_id=student_id,
                name=args.get('name'),
                class_name=args.get('class_name'),
                face_image_base64=args.get('face_image_base64'),
                image_format=args.get('image_format', 'jpg')
            )
            return success_response(student.to_dict(), '学生信息更新成功')
        except ValueError as e:
            return error_response(str(e), BizCode.NOT_FOUND)
        except Exception as e:
            return error_response(f'更新学生信息异常: {str(e)}', BizCode.INTERNAL_ERROR)

    @jwt_required()
    def delete(self, student_id):
        current_user = get_current_user()
        if not current_user or current_user.role not in ('teacher', 'admin'):
            return error_response('无权限执行此操作', BizCode.FORBIDDEN)

        try:
            self.student_service.delete_student(student_id)
            return success_response(message='学生删除成功')
        except ValueError as e:
            return error_response(str(e), BizCode.NOT_FOUND)
        except Exception as e:
            return error_response(f'删除学生异常: {str(e)}', BizCode.INTERNAL_ERROR)


class StudentBatchImportResource(Resource):
    def __init__(self):
        self.student_service = StudentService()

    @jwt_required()
    def post(self):
        current_user = get_current_user()
        if not current_user or current_user.role not in ('teacher', 'admin'):
            return error_response('无权限执行此操作', BizCode.FORBIDDEN)

        data = request.get_json()
        if not data or 'students' not in data:
            return error_response('请提供学生列表数据', BizCode.MISSING_FIELD)

        students_data = data['students']
        if not isinstance(students_data, list) or len(students_data) == 0:
            return error_response('学生列表不能为空', BizCode.BAD_REQUEST)

        try:
            result = self.student_service.batch_import(students_data)
            if result['fail_count'] > 0:
                return success_response(result, '批量导入部分成功', BizCode.BATCH_PARTIAL_FAIL)
            return success_response(result, '批量导入全部成功')
        except Exception as e:
            return error_response(f'批量导入异常: {str(e)}', BizCode.INTERNAL_ERROR)


class StudentBatchImportExcelResource(Resource):
    def __init__(self):
        self.student_service = StudentService()

    @jwt_required()
    def post(self):
        current_user = get_current_user()
        if not current_user or current_user.role not in ('teacher', 'admin'):
            return error_response('无权限执行此操作', BizCode.FORBIDDEN)

        if 'file' not in request.files:
            return error_response('请上传Excel文件', BizCode.MISSING_FIELD)

        file = request.files['file']
        if not file.filename.endswith(('.xlsx', '.xls')):
            return error_response('仅支持xlsx/xls格式', BizCode.UNSUPPORTED_FORMAT)

        try:
            df = pd.read_excel(file)
            required_cols = {'student_id', 'name', 'class_name'}
            if not required_cols.issubset(df.columns):
                return error_response(
                    f'Excel缺少必要列: {required_cols - set(df.columns)}',
                    BizCode.EXCEL_TEMPLATE_ERROR
                )

            students_data = []
            for _, row in df.iterrows():
                item = {
                    'student_id': str(row['student_id']),
                    'name': str(row['name']),
                    'class_name': str(row['class_name']),
                    'face_image_base64': str(row.get('face_image_base64', '')) if pd.notna(row.get('face_image_base64')) else '',
                    'username': str(row.get('username', '')) if pd.notna(row.get('username')) else None,
                    'password': str(row.get('password', '')) if pd.notna(row.get('password')) else None
                }
                students_data.append(item)

            result = self.student_service.batch_import(students_data)
            if result['fail_count'] > 0:
                return success_response(result, '批量导入部分成功', BizCode.BATCH_PARTIAL_FAIL)
            return success_response(result, '批量导入全部成功')
        except Exception as e:
            return error_response(f'Excel导入异常: {str(e)}', BizCode.INTERNAL_ERROR)


class StudentBatchImportPhotoZipResource(Resource):
    def __init__(self):
        self.student_service = StudentService()

    @jwt_required()
    def post(self):
        current_user = get_current_user()
        if not current_user or current_user.role not in ('teacher', 'admin'):
            return error_response('无权限执行此操作', BizCode.FORBIDDEN)

        if 'file' not in request.files:
            return error_response('请上传学生照片压缩包', BizCode.MISSING_FIELD)

        file = request.files['file']
        if not file.filename:
            return error_response('请上传学生照片压缩包', BizCode.MISSING_FIELD)
        if not file.filename.lower().endswith('.zip'):
            return error_response('仅支持 zip 格式压缩包', BizCode.UNSUPPORTED_FORMAT)

        try:
            result = self.student_service.batch_import_photo_zip(file)
            if result['fail_count'] > 0:
                return success_response(result, '批量导入部分成功')
            return success_response(result, '批量导入全部成功')
        except ValueError as e:
            return error_response(str(e), BizCode.ZIP_FORMAT_ERROR)
        except Exception as e:
            return error_response(f'学生照片批量导入异常: {str(e)}', BizCode.INTERNAL_ERROR)
