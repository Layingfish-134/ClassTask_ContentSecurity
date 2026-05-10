from flask import send_file, send_from_directory, request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.report_service import ReportService
from app.dto.request.parsers import report_query_parser
from app.dto.response.common import error_response, BizCode
from app.utils.permission import get_current_user
from io import BytesIO
import os


class AttendanceSummaryExportResource(Resource):
    def __init__(self):
        self.report_service = ReportService()

    @jwt_required()
    def get(self):
        args = report_query_parser.parse_args()
        current_user = get_current_user()
        if not current_user or current_user.role not in ('teacher', 'admin'):
            return error_response('无权限导出报表', BizCode.FORBIDDEN)

        start_time = args.get('start_time')
        end_time = args.get('end_time')

        if not start_time or not end_time:
            return error_response('开始时间和结束时间不能为空', BizCode.MISSING_FIELD)

        try:
            excel_data = self.report_service.export_attendance_summary_report(
                class_name=args.get('class_name'),
                start_time=start_time,
                end_time=end_time
            )
            output = BytesIO(excel_data)
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name='attendance_summary_report.xlsx'
            )
        except Exception as e:
            return error_response(f'导出考勤汇总报表异常: {str(e)}', BizCode.INTERNAL_ERROR)


class StudentActivityExportResource(Resource):
    def __init__(self):
        self.report_service = ReportService()

    @jwt_required()
    def get(self):
        args = report_query_parser.parse_args()
        current_user = get_current_user()
        if not current_user or current_user.role not in ('teacher', 'admin'):
            return error_response('无权限导出报表', BizCode.FORBIDDEN)

        student_id = args.get('student_id')
        if not student_id:
            return error_response('学生学号不能为空', BizCode.MISSING_FIELD)

        try:
            excel_data = self.report_service.export_student_activity_report(student_id=student_id)
            output = BytesIO(excel_data)
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'student_activity_report_{student_id}.xlsx'
            )
        except Exception as e:
            return error_response(f'导出学生活动参与报表异常: {str(e)}', BizCode.INTERNAL_ERROR)


class ActivityRecordExportResource(Resource):
    def __init__(self):
        self.report_service = ReportService()

    @jwt_required()
    def get(self):
        args = report_query_parser.parse_args()
        current_user = get_current_user()
        if not current_user or current_user.role not in ('teacher', 'admin'):
            return error_response('无权限导出报表', BizCode.FORBIDDEN)

        activity_name = args.get('activity_name')
        if not activity_name:
            return error_response('活动名称不能为空', BizCode.MISSING_FIELD)

        try:
            excel_data = self.report_service.export_activity_record_report(activity_name=activity_name)
            output = BytesIO(excel_data)
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'activity_record_report_{activity_name}.xlsx'
            )
        except Exception as e:
            return error_response(f'导出活动记录报表异常: {str(e)}', BizCode.INTERNAL_ERROR)


class AttendanceExportResource(Resource):
    def __init__(self):
        self.report_service = ReportService()

    @jwt_required()
    def get(self):
        args = report_query_parser.parse_args()
        current_user = get_current_user()
        if not current_user or current_user.role not in ('teacher', 'admin'):
            return error_response('无权限导出报表', BizCode.FORBIDDEN)

        start_time = args.get('start_time')
        end_time = args.get('end_time')

        if not start_time or not end_time:
            return error_response('开始时间和结束时间不能为空', BizCode.MISSING_FIELD)

        try:
            excel_data = self.report_service.export_attendance_report(
                class_name=args.get('class_name'),
                start_time=start_time,
                end_time=end_time
            )
            output = BytesIO(excel_data)
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name='attendance_report.xlsx'
            )
        except Exception as e:
            return error_response(f'导出考勤报表异常: {str(e)}', BizCode.INTERNAL_ERROR)


class ActivityFrequencyExportResource(Resource):
    def __init__(self):
        self.report_service = ReportService()

    @jwt_required()
    def get(self):
        args = report_query_parser.parse_args()
        current_user = get_current_user()
        if not current_user or current_user.role not in ('teacher', 'admin'):
            return error_response('无权限导出报表', BizCode.FORBIDDEN)

        try:
            excel_data = self.report_service.export_activity_frequency_report(
                class_name=args.get('class_name')
            )
            output = BytesIO(excel_data)
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name='activity_frequency_report.xlsx'
            )
        except Exception as e:
            return error_response(f'导出活动频次报表异常: {str(e)}', BizCode.INTERNAL_ERROR)


class FileAccessResource(Resource):
    @jwt_required()
    def get(self, filename):
        current_user = get_current_user()
        if not current_user:
            return error_response('未登录', BizCode.UNAUTHORIZED)

        upload_dir = os.getenv('UPLOAD_FOLDER', 'uploads/')
        filepath = os.path.join(upload_dir, filename)

        if not os.path.exists(filepath):
            return error_response('文件不存在', BizCode.NOT_FOUND)

        if current_user.role == 'student':
            from app.models.attendance_record import AttendanceRecord
            record = AttendanceRecord.query.filter_by(
                student_id=current_user.student_id,
                image_path=filepath
            ).first()
            if not record:
                return error_response('无权限访问该文件', BizCode.FORBIDDEN_FILE)

        try:
            return send_from_directory(
                os.path.abspath(upload_dir),
                filename,
                as_attachment=False
            )
        except Exception as e:
            return error_response(f'文件访问异常: {str(e)}', BizCode.INTERNAL_ERROR)
