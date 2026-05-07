import numpy as np
import json
import os


class FaceMatcher:
    def __init__(self):
        self.threshold = float(os.getenv('FACE_MATCH_THRESHOLD', 0.8))

    def match_features(self, feature1, feature2):
        feature1 = np.array(feature1, dtype=np.float64)
        feature2 = np.array(feature2, dtype=np.float64)

        if feature1.shape != feature2.shape:
            min_len = min(len(feature1), len(feature2))
            feature1 = feature1[:min_len]
            feature2 = feature2[:min_len]

        norm1 = np.linalg.norm(feature1)
        norm2 = np.linalg.norm(feature2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = np.dot(feature1, feature2) / (norm1 * norm2)
        similarity = max(0.0, min(1.0, float(similarity)))

        return similarity

    def find_best_match(self, input_feature, students):
        if not students:
            return None

        best_match = None
        best_score = 0.0

        input_feature = np.array(input_feature, dtype=np.float64)

        for student in students:
            if student.face_feature is None:
                continue

            try:
                stored_feature = json.loads(student.face_feature)
                stored_feature = np.array(stored_feature, dtype=np.float64)
            except (json.JSONDecodeError, TypeError):
                continue

            score = self.match_features(input_feature, stored_feature)

            if score > best_score:
                best_score = score
                best_match = student

        from app.dto.response.face_match_result import FaceMatchResult

        if best_match and best_score >= self.threshold:
            return FaceMatchResult(
                student_id=best_match.student_id,
                name=best_match.name,
                class_name=best_match.class_name,
                confidence=best_score * 100,
                matched=True
            )

        if best_match:
            return FaceMatchResult(
                student_id=best_match.student_id,
                name=best_match.name,
                class_name=best_match.class_name,
                confidence=best_score * 100,
                matched=False
            )

        return FaceMatchResult(matched=False)

    def find_all_matches(self, input_features_list, students, threshold=None):
        if threshold is None:
            threshold = self.threshold

        results = []
        for input_feature in input_features_list:
            match_result = self.find_best_match(input_feature, students)
            if match_result and match_result.confidence >= threshold * 100:
                results.append(match_result)
            else:
                from app.dto.response.face_match_result import FaceMatchResult
                results.append(FaceMatchResult(matched=False))

        return results
