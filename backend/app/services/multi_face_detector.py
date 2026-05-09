import cv2
import numpy as np
import os

from app.services.face_feature_extractor import SCRFDDetector


def _get_backend_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _resolve_model_path(path_value):
    if os.path.isabs(path_value):
        return path_value

    backend_root = _get_backend_root()
    project_root = os.path.dirname(backend_root)
    candidates = [
        os.path.normpath(os.path.join(backend_root, path_value)),
        os.path.normpath(os.path.join(project_root, path_value)),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return candidates[0]


def _find_model_file(path_value, filename, fallback_dir):
    primary_dir = _resolve_model_path(path_value)
    primary_file = os.path.join(primary_dir, filename)
    if os.path.exists(primary_file):
        return primary_file

    fallback_file = os.path.join(_resolve_model_path(fallback_dir), filename)
    if os.path.exists(fallback_file):
        return fallback_file

    return primary_file


class MultiFaceDetector:
    def __init__(self):
        self.detector = None
        self._init_detector()

    def _init_detector(self):
        try:
            import onnxruntime as ort
        except ImportError:
            return

        try:
            scrfd_path = os.getenv(
                'FACE_DETECTION_MODEL_PATH', 'models/scrfd/'
            )
            model_file = _find_model_file(
                scrfd_path,
                'scrfd_10g_bnkps.onnx',
                'models/scrfd/'
            )
            if os.path.exists(model_file):
                self.detector = SCRFDDetector(model_file)
        except Exception:
            self.detector = None

    def detect_faces(self, image_data):
        if isinstance(image_data, bytes):
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        else:
            image = image_data

        if image is None:
            return []

        if self.detector is not None:
            return self._detect_scrfd(image)
        else:
            return self._detect_opencv(image)

    def _detect_scrfd(self, image):
        try:
            results = self.detector.detect(
                image, threshold=0.5, nms_thresh=0.4
            )

            if not results:
                return self._detect_opencv(image)

            faces = []
            for result in results:
                x1, y1, x2, y2 = result['box']
                x1, y1 = max(0, x1), max(0, y1)
                y2 = min(image.shape[0], y2)
                x2 = min(image.shape[1], x2)

                face_image = image[y1:y2, x1:x2]
                if face_image.size == 0:
                    continue

                kps = result.get('keypoints', [])
                keypoints = {}
                if kps:
                    keypoint_names = [
                        'left_eye', 'right_eye', 'nose',
                        'left_mouth', 'right_mouth'
                    ]
                    for i, name in enumerate(keypoint_names):
                        if i < len(kps):
                            keypoints[name] = {
                                'x': int(kps[i][0]),
                                'y': int(kps[i][1])
                            }

                faces.append({
                    'box': (x1, y1, x2, y2),
                    'confidence': result['confidence'],
                    'face_image': face_image,
                    'keypoints': keypoints
                })

            return faces
        except Exception:
            return self._detect_opencv(image)

    def _detect_opencv(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        cascade_path = (
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        face_cascade = cv2.CascadeClassifier(cascade_path)
        detected = face_cascade.detectMultiScale(
            gray, 1.1, 5, minSize=(30, 30)
        )

        faces = []
        for (x, y, w, h) in detected:
            face_image = image[y:y + h, x:x + w]
            if face_image.size == 0:
                continue

            faces.append({
                'box': (x, y, x + w, y + h),
                'confidence': 0.85,
                'face_image': face_image,
                'keypoints': {}
            })

        return faces

    def detect_faces_from_base64(self, image_base64):
        from app.utils.image_utils import base64_to_image
        image = base64_to_image(image_base64)
        if image is None:
            return []
        return self.detect_faces(image)
