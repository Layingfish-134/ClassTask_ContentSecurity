from flask_restful import Resource
from flask_jwt_extended import jwt_required
from app.services.report_service import ReportService
from app.dto.request.parsers import emotion_query_parser
from app.dto.response.common import success_response, error_response, BizCode
from app.utils.permission import get_current_user


class EmotionStatisticsResource(Resource):
    def __init__(self):
        self.report_service = ReportService()

    @jwt_required()
    def get(self):
        args = emotion_query_parser.parse_args()
        current_user = get_current_user()
        if current_user and current_user.role == 'student':
            return error_response('学生账号无权进入数据分析', BizCode.FORBIDDEN)

        class_name = args.get('class_name')
        student_id = args.get('student_id')

        try:
            result = self.report_service.get_emotion_statistics(
                class_name=class_name,
                student_id=student_id,
                source_type=args.get('source_type'),
                start_time=args.get('start_time'),
                end_time=args.get('end_time')
            )
            return success_response(result)
        except Exception as e:
            return error_response(f'查询情绪统计异常: {str(e)}', BizCode.INTERNAL_ERROR)


class EmotionTrendResource(Resource):
    def __init__(self):
        self.report_service = ReportService()

    @jwt_required()
    def get(self):
        args = emotion_query_parser.parse_args()
        current_user = get_current_user()
        if current_user and current_user.role == 'student':
            return error_response('学生账号无权进入数据分析', BizCode.FORBIDDEN)

        class_name = args.get('class_name')
        student_id = args.get('student_id')

        try:
            result = self.report_service.get_emotion_trend(
                class_name=class_name,
                student_id=student_id,
                source_type=args.get('source_type'),
                start_time=args.get('start_time'),
                end_time=args.get('end_time')
            )
            return success_response(result)
        except Exception as e:
            return error_response(f'查询情绪趋势异常: {str(e)}', BizCode.INTERNAL_ERROR)
