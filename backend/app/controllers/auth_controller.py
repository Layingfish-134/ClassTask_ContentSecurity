from flask_restful import Resource
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from app.models.user import User
from app.dto.request.parsers import login_parser, refresh_parser
from app.dto.response.common import success_response, error_response, BizCode
from app.config.database_config import db
import bcrypt


class LoginResource(Resource):
    def post(self):
        args = login_parser.parse_args()
        username = args['username']
        password = args['password']

        user = User.query.filter_by(username=username).first()
        if not user:
            return error_response('用户名或密码错误', BizCode.UNAUTHORIZED)

        if user.status != 1:
            return error_response('账号已停用', BizCode.ACCOUNT_DISABLED)

        if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return error_response('用户名或密码错误', BizCode.UNAUTHORIZED)

        access_token = create_access_token(identity=user.user_id)
        refresh_token = create_refresh_token(identity=user.user_id)

        return success_response({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user_id': user.user_id,
            'username': user.username,
            'role': user.role,
            'student_id': user.student_id
        }, '登录成功')


class RefreshResource(Resource):
    def post(self):
        args = refresh_parser.parse_args()
        refresh_token = args['refresh_token']

        try:
            from flask_jwt_extended import decode_token
            decoded = decode_token(refresh_token)
            user_id = decoded['sub']

            user = User.query.get(user_id)
            if not user or user.status != 1:
                return error_response('用户不存在或已停用', BizCode.UNAUTHORIZED)

            access_token = create_access_token(identity=user_id)
            refresh_token_new = create_refresh_token(identity=user_id)

            return success_response({
                'access_token': access_token,
                'refresh_token': refresh_token_new
            }, '令牌刷新成功')
        except Exception:
            return error_response('刷新令牌无效或已过期', BizCode.TOKEN_EXPIRED)


class CurrentUserResource(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return error_response('用户不存在', BizCode.NOT_FOUND)
        result = user.to_dict()
        if user.student_info:
            result['student_info'] = user.student_info.to_dict()
        return success_response(result)


def init_default_users():
    default_accounts = [
        {
            'user_id': 'admin',
            'username': 'admin',
            'password': 'admin123',
            'role': 'admin',
            'student_id': None
        },
        {
            'user_id': 'teacher001',
            'username': 'teacher001',
            'password': '123456',
            'role': 'teacher',
            'student_id': None
        }
    ]

    for account in default_accounts:
        existing = User.query.filter_by(username=account['username']).first()
        if not existing:
            hashed = bcrypt.hashpw(
                account['password'].encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')
            user = User(
                user_id=account['user_id'],
                username=account['username'],
                password_hash=hashed,
                role=account['role'],
                student_id=account['student_id'],
                status=1
            )
            db.session.add(user)

    db.session.commit()
