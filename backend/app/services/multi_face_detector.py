import cv2
import numpy as np

try:
    from mtcnn import MTCNN
    MTCNN_AVAILABLE = True
except ImportError:
    MTCNN_AVAILABLE = False


class MultiFaceDetector:
    def __init__(self):
        self.detector = None
        self._init_detector()

    def _init_detector(self):
        if MTCNN_AVAILABLE:
            self.detector = MTCNN()

    def detect_faces(self, image_data):
        if isinstance(image_data, bytes):
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        else:
            image = image_data

        if image is None:
            return []

        if self.detector is not None:
            return self._detect_mtcnn(image)
        else:
            return self._detect_opencv(image)

    def _detect_mtcnn(self, image):
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.detector.detect_faces(rgb_image)

        faces = []
        for result in results:
            x1, y1, width, height = result['box']
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = x1 + width, y1 + height

            face_image = image[y1:y2, x1:x2]
            if face_image.size == 0:
                continue

            faces.append({
                'box': (x1, y1, x2, y2),
                'confidence': result['confidence'],
                'face_image': face_image,
                'keypoints': result.get('keypoints', {})
            })

        return faces

    def _detect_opencv(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_path)
        detected = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))

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
