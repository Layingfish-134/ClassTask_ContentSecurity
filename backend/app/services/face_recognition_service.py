from app.services.liveness_detector import LivenessDetector
from app.services.face_feature_extractor import FaceFeatureExtractor
from app.services.face_matcher import FaceMatcher
from app.services.multi_face_detector import MultiFaceDetector
from app.services.emotion_classifier import EmotionClassifier
from app.dto.response.face_match_result import FaceMatchResult
from app.dto.response.emotion_result import EmotionResult
from app.repositories.student_repository import StudentRepository
from app.utils.image_utils import base64_to_image


class FaceRecognitionService:
    def __init__(self):
        self.liveness_detector = LivenessDetector()
        self.feature_extractor = FaceFeatureExtractor()
        self.face_matcher = FaceMatcher()
        self.multi_face_detector = MultiFaceDetector()
        self.emotion_classifier = EmotionClassifier()

    def recognize_single_face(self, image_data, target_student_id=None):
        if isinstance(image_data, str):
            image = base64_to_image(image_data)
        elif isinstance(image_data, bytes):
            import numpy as np
            import cv2
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        else:
            image = image_data

        if image is None:
            return FaceMatchResult(matched=False), EmotionResult()

        face_result = self.feature_extractor.detect_face(image)
        if face_result is None:
            return FaceMatchResult(matched=False), EmotionResult()

        keypoints = face_result.get('keypoints', [])
        feature = self.feature_extractor.extract_feature(
            face_result['face_image'],
            original_image=image,
            keypoints=keypoints if keypoints else None
        )
        if feature is None:
            return FaceMatchResult(matched=False), EmotionResult()

        if target_student_id:
            student = StudentRepository.find_by_id(target_student_id)
            if student and student.face_feature:
                students = [student]
            else:
                return FaceMatchResult(matched=False), EmotionResult()
        else:
            students = StudentRepository.find_all_with_features()

        match_result = self.face_matcher.find_best_match(feature, students)

        emotion_result = self.emotion_classifier.classify_emotion(face_result['face_image'])

        return match_result, emotion_result

    def recognize_multiple_faces(self, image_data):
        if isinstance(image_data, str):
            image = base64_to_image(image_data)
        elif isinstance(image_data, bytes):
            import numpy as np
            import cv2
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        else:
            image = image_data

        if image is None:
            return []

        faces = self.multi_face_detector.detect_faces(image)
        if not faces:
            return []

        students = StudentRepository.find_all_with_features()
        results = []

        for face_info in faces:
            face_image = face_info['face_image']
            if face_image.size == 0:
                continue

            keypoints = face_info.get('keypoints', {})
            keypoints_list = None
            if keypoints:
                keypoints_list = []
                for name in [
                    'left_eye', 'right_eye', 'nose',
                    'left_mouth', 'right_mouth'
                ]:
                    if name in keypoints:
                        keypoints_list.append([
                            keypoints[name]['x'],
                            keypoints[name]['y']
                        ])

            feature = self.feature_extractor.extract_feature(
                face_image,
                original_image=image,
                keypoints=keypoints_list if keypoints_list else None
            )
            if feature is None:
                continue

            match_result = self.face_matcher.find_best_match(feature, students)
            emotion_result = self.emotion_classifier.classify_emotion(face_image)

            results.append({
                'match': match_result,
                'emotion': emotion_result,
                'confidence': face_info.get('confidence', 0.0)
            })

        return results
