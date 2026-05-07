from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.report_service import ReportService
from app.dto.request.parsers import group_photo_parser, group_photo_query_parser
from app.dto.response.common import success_response, error_response, paginated_response, BizCode
from app.utils.permission import get_current_user


class GroupPhotoRecognizeResource(Resource):
    def __init__(self):
        self.report_service = ReportService()

    @jwt_required()
    def post(self):
        args = group_photo_parser.parse_args()
        photo_base64 = args['photo_base64']
        image_format = args['image_format']
        photo_name = args.get('photo_name', '')
        activity_name = args.get('activity_name', '')
        activity_time = args.get('activity_time')

        if not photo_base64:
            return error_response('合照图像数据不能为空', BizCode.MISSING_FIELD)

        current_user = get_current_user()

        try:
            result = self.report_service.process_group_photo(
                photo_base64=photo_base64,
                image_format=image_format,
                photo_name=photo_name,
                activity_name=activity_name,
                activity_time=activity_time,
                created_by=current_user.user_id if current_user else None
            )
            return success_response(result, '识别完成')
        except Exception as e:
            return error_response(f'合照识别异常: {str(e)}', BizCode.INTERNAL_ERROR)


class GroupPhotoRecordResource(Resource):
    def __init__(self):
        self.report_service = ReportService()

    @jwt_required()
    def get(self):
        args = group_photo_query_parser.parse_args()
        current_user = get_current_user()

        class_name = args.get('class_name')
        if current_user and current_user.role == 'student':
            class_name = current_user.student_info.class_name if current_user.student_info else None

        try:
            records, size, next_cursor, has_more = self.report_service.get_group_photo_records(
                activity_name=args.get('activity_name'),
                class_name=class_name,
                start_time=args.get('start_time'),
                end_time=args.get('end_time'),
                cursor=args.get('cursor'),
                size=args.get('size', 20)
            )
            return paginated_response(records, size, next_cursor, has_more)
        except Exception as e:
            return error_response(f'查询合照记录异常: {str(e)}', BizCode.INTERNAL_ERROR)
