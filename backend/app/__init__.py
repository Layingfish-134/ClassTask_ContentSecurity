import os
import logging
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_restful import Api

from app.config.database_config import init_db
from app.exception.global_exception_handler import register_error_handlers
from app.controllers.auth_controller import init_default_users


def create_app():
    app = Flask(__name__)

    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if os.path.exists(env_path):
        from dotenv import load_dotenv
        load_dotenv(env_path)

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'attendance-system-secret-key')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-attendance-secret-key')
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads/')
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 10485760))
    app.config['PROPAGATE_EXCEPTIONS'] = True

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    jwt = JWTManager(app)
    _register_jwt_handlers(jwt)

    init_db(app)

    register_error_handlers(app)

    api = Api(app, prefix='/api')

    _register_routes(api)

    with app.app_context():
        try:
            init_default_users()
            app.logger.info('默认用户初始化完成')
        except Exception as e:
            app.logger.warning(f'默认用户初始化失败（数据库可能未就绪）: {e}')

    return app


def _register_jwt_handlers(jwt):
    from app.dto.response.common import error_response, BizCode

    @jwt.unauthorized_loader
    def handle_missing_token(reason):
        return error_response('未登录或登录状态已失效', BizCode.UNAUTHORIZED)

    @jwt.invalid_token_loader
    def handle_invalid_token(reason):
        return error_response('登录状态无效，请重新登录', BizCode.UNAUTHORIZED)

    @jwt.expired_token_loader
    def handle_expired_token(jwt_header, jwt_payload):
        return error_response('登录状态已过期，请重新登录', BizCode.TOKEN_EXPIRED)

    @jwt.revoked_token_loader
    def handle_revoked_token(jwt_header, jwt_payload):
        return error_response('登录状态已失效，请重新登录', BizCode.UNAUTHORIZED)

    @jwt.needs_fresh_token_loader
    def handle_needs_fresh_token(jwt_header, jwt_payload):
        return error_response('需要重新登录后继续操作', BizCode.UNAUTHORIZED)


def _register_routes(api):
    from app.controllers.attendance_controller import CheckinResource, AttendanceRecordResource
    from app.controllers.student_controller import (
        StudentListResource, StudentDetailResource,
        StudentBatchImportResource, StudentBatchImportExcelResource
    )
    from app.controllers.group_photo_controller import GroupPhotoRecognizeResource, GroupPhotoRecordResource
    from app.controllers.emotion_controller import EmotionStatisticsResource, EmotionTrendResource
    from app.controllers.report_controller import (
        AttendanceExportResource, ActivityFrequencyExportResource, FileAccessResource
    )
    from app.controllers.auth_controller import LoginResource, RefreshResource, CurrentUserResource

    api.add_resource(LoginResource, '/auth/login')
    api.add_resource(RefreshResource, '/auth/refresh')
    api.add_resource(CurrentUserResource, '/auth/me')

    api.add_resource(CheckinResource, '/attendance/checkin')
    api.add_resource(AttendanceRecordResource, '/attendance/records')

    api.add_resource(StudentListResource, '/students')
    api.add_resource(StudentDetailResource, '/students/<string:student_id>')
    api.add_resource(StudentBatchImportResource, '/students/batch-import')
    api.add_resource(StudentBatchImportExcelResource, '/students/batch-import/excel')

    api.add_resource(GroupPhotoRecognizeResource, '/group-photo/recognize')
    api.add_resource(GroupPhotoRecordResource, '/group-photo/records')

    api.add_resource(EmotionStatisticsResource, '/emotion/statistics')
    api.add_resource(EmotionTrendResource, '/emotion/trend')

    api.add_resource(AttendanceExportResource, '/reports/attendance/export')
    api.add_resource(ActivityFrequencyExportResource, '/reports/activity-frequency/export')

    api.add_resource(FileAccessResource, '/files/<string:filename>')
