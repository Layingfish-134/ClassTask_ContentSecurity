import cv2
import numpy as np
import os
import torch

try:
    from mtcnn import MTCNN
    MTCNN_AVAILABLE = True
except ImportError:
    MTCNN_AVAILABLE = False

try:
    from facenet_pytorch import InceptionResnetV1
    FACENET_AVAILABLE = True
except ImportError:
    FACENET_AVAILABLE = False


class FaceFeatureExtractor:
    def __init__(self):
        self.detector = None
        self.resnet = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self._init_models()

    def _init_models(self):
        if MTCNN_AVAILABLE:
            self.detector = MTCNN()
        if FACENET_AVAILABLE:
            self.resnet = InceptionResnetV1(
                pretrained='vggface2',
                device=self.device
            ).eval()

    def detect_face(self, image):
        if self.detector is None:
            return self._detect_face_opencv(image)

        if isinstance(image, np.ndarray):
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            rgb_image = image

        results = self.detector.detect_faces(rgb_image)
        if not results:
            return None

        x1, y1, width, height = results[0]['box']
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = x1 + width, y1 + height

        return {
            'box': (x1, y1, x2, y2),
            'confidence': results[0]['confidence'],
            'face_image': image[y1:y2, x1:x2]
        }

    def _detect_face_opencv(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_path)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces) == 0:
            return None

        x, y, w, h = faces[0]
        return {
            'box': (x, y, x + w, y + h),
            'confidence': 0.9,
            'face_image': image[y:y + h, x:x + w]
        }

    def extract_feature(self, face_image):
        if self.resnet is None:
            return self._extract_feature_opencv(face_image)

        try:
            face_resized = cv2.resize(face_image, (160, 160))
            face_rgb = cv2.cvtColor(face_resized, cv2.COLOR_BGR2RGB)
            face_tensor = torch.from_numpy(face_rgb).permute(2, 0, 1).float()
            face_tensor = (face_tensor - 127.5) / 128.0
            face_tensor = face_tensor.unsqueeze(0).to(self.device)

            with torch.no_grad():
                feature = self.resnet(face_tensor)

            return feature.cpu().numpy().flatten()
        except Exception:
            return self._extract_feature_opencv(face_image)

    def _extract_feature_opencv(self, face_image):
        face_resized = cv2.resize(face_image, (128, 128))
        gray = cv2.cvtColor(face_resized, cv2.COLOR_BGR2GRAY)
        equalized = cv2.equalizeHist(gray)
        feature = equalized.flatten().astype(np.float32) / 255.0
        return feature

    def extract_feature_from_base64(self, image_base64):
        from app.utils.image_utils import base64_to_image
        image = base64_to_image(image_base64)
        if image is None:
            return None

        face_result = self.detect_face(image)
        if face_result is None:
            return None

        return self.extract_feature(face_result['face_image'])
