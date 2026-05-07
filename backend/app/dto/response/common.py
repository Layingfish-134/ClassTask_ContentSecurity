import uuid
from flask import jsonify


def generate_request_id():
    return f"req_{uuid.uuid4().hex[:20]}"


def success_response(data=None, message='success', code=200, request_id=None):
    return {
        'code': code,
        'message': message,
        'data': data,
        'request_id': request_id or generate_request_id()
    }, code


def error_response(message='操作失败', code=400, data=None, request_id=None):
    return {
        'code': code,
        'message': message,
        'data': data,
        'request_id': request_id or generate_request_id()
    }, _http_status_from_code(code)


def paginated_response(records, size=20, next_cursor=None, has_more=False, message='success', request_id=None):
    data = {
        'records': records,
        'size': size,
        'next_cursor': next_cursor,
        'has_more': has_more
    }
    return {
        'code': 200,
        'message': message,
        'data': data,
        'request_id': request_id or generate_request_id()
    }, 200


def _http_status_from_code(biz_code):
    if biz_code >= 50000:
        return 500
    elif biz_code >= 42200:
        if biz_code == 42207:
            return 504
        return 422
    elif biz_code >= 40900:
        return 409
    elif biz_code >= 40300:
        return 403
    elif biz_code >= 40100:
        return 401
    elif biz_code >= 40000:
        return 400
    return 400


class BizCode:
    SUCCESS = 200
    CREATED = 201
    BAD_REQUEST = 40000
    MISSING_FIELD = 40001
    UNSUPPORTED_FORMAT = 40002
    FILE_TOO_LARGE = 40003
    EXCEL_TEMPLATE_ERROR = 40004
    ZIP_FORMAT_ERROR = 40005
    UNAUTHORIZED = 40100
    TOKEN_EXPIRED = 40101
    ACCOUNT_DISABLED = 40102
    FORBIDDEN = 40300
    FORBIDDEN_FILE = 40301
    NOT_FOUND = 40400
    CONFLICT = 40900
    NO_FACE = 42201
    MULTIPLE_FACES = 42202
    LIVENESS_FAILED = 42203
    PHOTO_ATTACK = 42204
    VIDEO_REPLAY = 42205
    FACE_NOT_MATCHED = 42206
    RECOGNITION_TIMEOUT = 42207
    BATCH_PARTIAL_FAIL = 42208
    INTERNAL_ERROR = 50000
    DB_UNAVAILABLE = 50300
