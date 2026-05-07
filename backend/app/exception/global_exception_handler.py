from flask import jsonify
import logging
import traceback

logger = logging.getLogger(__name__)


class AppException(Exception):
    def __init__(self, message='系统异常', code=400, data=None):
        self.message = message
        self.code = code
        self.data = data
        super().__init__(self.message)


class LivenessCheckFailedException(AppException):
    def __init__(self, message='活体检测失败，疑似照片攻击'):
        super().__init__(message=message, code=400)


class FaceNotFoundException(AppException):
    def __init__(self, message='未检测到人脸'):
        super().__init__(message=message, code=400)


class FaceMatchFailedException(AppException):
    def __init__(self, message='人脸比对失败，未匹配到学生'):
        super().__init__(message=message, code=400)


class ImageDecodeException(AppException):
    def __init__(self, message='图像解码失败'):
        super().__init__(message=message, code=400)


class StudentExistsException(AppException):
    def __init__(self, message='学号已存在'):
        super().__init__(message=message, code=400)


class StudentNotFoundException(AppException):
    def __init__(self, message='学生不存在'):
        super().__init__(message=message, code=404)


class UnauthorizedException(AppException):
    def __init__(self, message='未授权访问'):
        super().__init__(message=message, code=401)


class ForbiddenException(AppException):
    def __init__(self, message='权限不足'):
        super().__init__(message=message, code=403)


def register_error_handlers(app):
    @app.errorhandler(AppException)
    def handle_app_exception(e):
        logger.warning(f'AppException: {e.message}')
        response = jsonify({
            'code': e.code,
            'message': e.message,
            'data': e.data
        })
        response.status_code = e.code
        return response

    @app.errorhandler(400)
    def handle_bad_request(e):
        return jsonify({
            'code': 400,
            'message': '请求参数错误',
            'data': None
        }), 400

    @app.errorhandler(401)
    def handle_unauthorized(e):
        return jsonify({
            'code': 401,
            'message': '未授权访问',
            'data': None
        }), 401

    @app.errorhandler(403)
    def handle_forbidden(e):
        return jsonify({
            'code': 403,
            'message': '权限不足',
            'data': None
        }), 403

    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify({
            'code': 404,
            'message': '请求的资源不存在',
            'data': None
        }), 404

    @app.errorhandler(500)
    def handle_internal_error(e):
        logger.error(f'Internal Server Error: {traceback.format_exc()}')
        return jsonify({
            'code': 500,
            'message': '服务器内部错误',
            'data': None
        }), 500

    @app.errorhandler(Exception)
    def handle_generic_exception(e):
        logger.error(f'Unhandled Exception: {traceback.format_exc()}')
        return jsonify({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': None
        }), 500
