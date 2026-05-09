import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_ROOT = os.path.join(PROJECT_ROOT, 'backend')
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app import create_app  # noqa: E402
from app.dto.response.face_match_result import FaceMatchResult  # noqa: E402
from app.services.face_matcher import FaceMatcher  # noqa: E402


class FakeStudent:
    def __init__(self, face_feature):
        self.student_id = '20240001'
        self.name = '测试学生'
        self.class_name = '测试班'
        self.face_feature = face_feature


class BackendSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def login_headers(self):
        response = self.client.post(
            '/api/auth/login',
            json={'username': 'admin', 'password': 'demo_hash_123456'}
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['code'], 200)
        token = data['data']['access_token']
        return {'Authorization': f'Bearer {token}'}

    def test_auth_and_read_endpoints(self):
        headers = self.login_headers()

        for endpoint in (
            '/api/auth/me',
            '/api/students',
            '/api/attendance/records',
            '/api/group-photo/records',
        ):
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint, headers=headers)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.get_json()['code'], 200)

    def test_invalid_or_missing_token_returns_401(self):
        cases = (
            ({}, '未登录'),
            ({'Authorization': 'Bearer bad.token.value'}, '重新登录'),
        )

        for headers, message_part in cases:
            with self.subTest(headers=headers):
                response = self.client.get('/api/auth/me', headers=headers)
                self.assertEqual(response.status_code, 401)
                data = response.get_json()
                self.assertEqual(data['code'], 40100)
                self.assertIn(message_part, data['message'])

    def test_emotion_endpoints_accept_empty_filters(self):
        headers = self.login_headers()

        for endpoint in ('/api/emotion/statistics', '/api/emotion/trend'):
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint, headers=headers)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.get_json()['code'], 200)

    def test_report_exports_return_xlsx(self):
        headers = self.login_headers()

        for endpoint in (
            '/api/reports/attendance/export?start_time=2026-01-01T00:00:00&end_time=2026-12-31T23:59:59',
            '/api/reports/activity-frequency/export',
        ):
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint, headers=headers)
                self.assertEqual(response.status_code, 200)
                self.assertIn(
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    response.content_type
                )
                self.assertTrue(response.data.startswith(b'PK'))

    def test_face_matcher_accepts_json_column_lists(self):
        matcher = FaceMatcher()
        result = matcher.find_best_match([1.0, 0.0, 0.0], [FakeStudent([1.0, 0.0, 0.0])])
        self.assertIsInstance(result, FaceMatchResult)
        self.assertTrue(result.matched)
        self.assertEqual(result.student_id, '20240001')


if __name__ == '__main__':
    unittest.main()
