from flask_restful import Resource
from flask_jwt_extended import jwt_required
from app.services.attendance_service import AttendanceService
from app.dto.request.parsers import checkin_parser, attendance_query_parser
from app.dto.response.common import success_response, error_response, BizCode
from app.utils.permission import get_current_user, enforce_student_data_access


class CheckinResource(Resource):
    def __init__(self):
        self.attendance_service = AttendanceService()

    @jwt_required()
    def post(self):
        args = checkin_parser.parse_args()
        image_base64 = args['image_base64']
        image_format = args['image_format']
        idempotency_key = args.get('idempotency_key')
        device_id = args.get('device_id')
        capture_time = args.get('capture_time')
        frames_base64 = args.get('frames_base64')

        if not image_base64:
            return error_response('人脸图像数据不能为空', BizCode.MISSING_FIELD)

        current_user = get_current_user()

        try:
            result, biz_code = self.attendance_service.checkin(
                image_base64=image_base64,
                image_format=image_format,
                idempotency_key=idempotency_key,
                device_id=device_id,
                capture_time=capture_time,
                frames_base64=frames_base64,
                current_user=current_user
            )

            if biz_code == BizCode.SUCCESS:
                return success_response(result, '考勤成功')
            elif biz_code == BizCode.CONFLICT:
                return error_response('重复请求', BizCode.CONFLICT, result)
            elif biz_code in (BizCode.PHOTO_ATTACK, BizCode.VIDEO_REPLAY, BizCode.LIVENESS_FAILED):
                return error_response(
                    '活体检测失败，疑似伪造攻击' if biz_code != BizCode.LIVENESS_FAILED else '活体检测未通过',
                    biz_code, result
                )
            elif biz_code == BizCode.FACE_NOT_MATCHED:
                if current_user and current_user.role == 'student':
                    return error_response('人脸比对失败，请使用本人账号签到', biz_code, result)
                else:
                    return error_response('人脸比对失败，未匹配到学生', biz_code, result)
            else:
                return error_response('考勤失败', biz_code, result)
        except Exception as e:
            return error_response(f'考勤处理异常: {str(e)}', BizCode.INTERNAL_ERROR)


class AttendanceRecordResource(Resource):
    def __init__(self):
        self.attendance_service = AttendanceService()

    @jwt_required()
    def get(self):
        args = attendance_query_parser.parse_args()
        current_user, err = enforce_student_data_access(args.get('student_id'))
        if err:
            return err
        if current_user and current_user.role == 'student':
            return error_response('学生账号仅允许实时签到，不能查询考勤记录', BizCode.FORBIDDEN)

        try:
            records, total, page, size = self.attendance_service.get_attendance_records(
                student_id=args.get('student_id') if (not current_user or current_user.role != 'student') else current_user.student_id,
                class_name=args.get('class_name'),
                start_time=args.get('start_time'),
                end_time=args.get('end_time'),
                status=args.get('status'),
                keyword=args.get('keyword'),
                page=args.get('page', 1),
                size=args.get('size', 20),
                current_user=current_user
            )
            return success_response({
                'records': records,
                'total': total,
                'page': page,
                'size': size
            })
        except Exception as e:
            return error_response(f'查询考勤记录异常: {str(e)}', BizCode.INTERNAL_ERROR)
