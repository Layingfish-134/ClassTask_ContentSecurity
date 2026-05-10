import cv2
import numpy as np
import os
import torch

try:
    from facenet_pytorch import MTCNN, InceptionResnetV1
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
        if FACENET_AVAILABLE:
            self.detector = MTCNN(
                image_size=160,
                margin=int(os.getenv('FACE_CROP_MARGIN', 24)),
                min_face_size=int(os.getenv('FACE_MIN_SIZE', 40)),
                thresholds=[
                    float(os.getenv('FACE_MTCNN_PNET_THRESHOLD', 0.6)),
                    float(os.getenv('FACE_MTCNN_RNET_THRESHOLD', 0.7)),
                    float(os.getenv('FACE_MTCNN_ONET_THRESHOLD', 0.7)),
                ],
                post_process=True,
                select_largest=True,
                keep_all=False,
                device=self.device
            )
            self.resnet = InceptionResnetV1(
                pretrained='vggface2',
                device=self.device
            ).eval()

    def detect_face(self, image):
        if self.detector is None:
            return self._detect_face_opencv(image)

        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        boxes, probs, landmarks = self.detector.detect(rgb_image, landmarks=True)
        if boxes is None or len(boxes) == 0:
            return None

        best_idx = int(np.argmax(probs))
        box = boxes[best_idx]
        x1, y1, x2, y2 = self._clip_box(box, image.shape)
        aligned_tensor = self._extract_aligned_tensor(rgb_image, box)

        return {
            'box': (x1, y1, x2, y2),
            'confidence': float(probs[best_idx]),
            'face_image': image[y1:y2, x1:x2],
            'aligned_tensor': aligned_tensor,
            'landmarks': landmarks[best_idx].tolist() if landmarks is not None else None
        }

    def _clip_box(self, box, image_shape):
        height, width = image_shape[:2]
        x1, y1, x2, y2 = box.astype(int)
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(width, x2), min(height, y2)
        return x1, y1, x2, y2

    def _extract_aligned_tensor(self, rgb_image, box):
        if self.detector is None:
            return None
        try:
            aligned = self.detector.extract(rgb_image, np.expand_dims(box, axis=0), None)
            if aligned is None:
                return None
            if isinstance(aligned, torch.Tensor) and aligned.ndim == 4:
                return aligned[0]
            return aligned
        except Exception:
            return None

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

    def extract_feature_from_detection(self, face_result):
        aligned_tensor = face_result.get('aligned_tensor') if face_result else None
        if aligned_tensor is not None and self.resnet is not None:
            try:
                return self._extract_feature_from_tensor(aligned_tensor)
            except Exception:
                pass

        return self.extract_feature(face_result['face_image'])

    def _extract_feature_from_tensor(self, face_tensor):
        if not isinstance(face_tensor, torch.Tensor):
            face_tensor = torch.from_numpy(face_tensor)

        if face_tensor.ndim == 3:
            face_tensor = face_tensor.unsqueeze(0)

        face_tensor = face_tensor.float().to(self.device)

        with torch.no_grad():
            feature = self.resnet(face_tensor)

        return feature.cpu().numpy().flatten()

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

        return self.extract_feature_from_detection(face_result)
