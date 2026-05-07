from functools import wraps
from flask import request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.models.user import User
from app.dto.response.common import error_response, BizCode


def require_roles(*allowed_roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            if not user:
                return error_response('用户不存在', BizCode.UNAUTHORIZED)
            if user.status != 1:
                return error_response('账号已停用', BizCode.ACCOUNT_DISABLED)
            if user.role not in allowed_roles:
                return error_response('无权限访问该资源', BizCode.FORBIDDEN)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def require_teacher_or_admin(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return error_response('用户不存在', BizCode.UNAUTHORIZED)
        if user.status != 1:
            return error_response('账号已停用', BizCode.ACCOUNT_DISABLED)
        if user.role not in ('teacher', 'admin'):
            return error_response('无权限访问该资源', BizCode.FORBIDDEN)
        return fn(*args, **kwargs)
    return wrapper


def get_current_user():
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        if user_id:
            return User.query.get(user_id)
    except Exception:
        pass
    return None


def enforce_student_data_access(query_student_id=None):
    user = get_current_user()
    if not user:
        return None, error_response('未登录', BizCode.UNAUTHORIZED)
    if user.status != 1:
        return None, error_response('账号已停用', BizCode.ACCOUNT_DISABLED)
    if user.role == 'student':
        if query_student_id and query_student_id != user.student_id:
            return None, error_response('无权限访问该资源', BizCode.FORBIDDEN)
        return user, None
    return user, None
