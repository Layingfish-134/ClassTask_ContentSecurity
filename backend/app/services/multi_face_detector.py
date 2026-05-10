import cv2
import numpy as np
import os
import torch

try:
    from facenet_pytorch import MTCNN
    MTCNN_AVAILABLE = True
except ImportError:
    MTCNN_AVAILABLE = False


class MultiFaceDetector:
    def __init__(self):
        self.detector = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self._init_detector()

    def _init_detector(self):
        if MTCNN_AVAILABLE:
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
                keep_all=True,
                device=self.device
            )

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
        boxes, probs, landmarks = self.detector.detect(rgb_image, landmarks=True)
        if boxes is None or len(boxes) == 0:
            return []

        aligned_tensors = self._extract_aligned_tensors(rgb_image, boxes)

        faces = []
        for index, box in enumerate(boxes):
            x1, y1, x2, y2 = self._clip_box(box, image.shape)

            face_image = image[y1:y2, x1:x2]
            if face_image.size == 0:
                continue

            faces.append({
                'box': (x1, y1, x2, y2),
                'confidence': float(probs[index]),
                'face_image': face_image,
                'aligned_tensor': aligned_tensors[index] if aligned_tensors is not None else None,
                'keypoints': landmarks[index].tolist() if landmarks is not None else {}
            })

        return faces

    def _clip_box(self, box, image_shape):
        height, width = image_shape[:2]
        x1, y1, x2, y2 = box.astype(int)
        x1, y1 = int(max(0, x1)), int(max(0, y1))
        x2, y2 = int(min(width, x2)), int(min(height, y2))
        return x1, y1, x2, y2

    def _extract_aligned_tensors(self, rgb_image, boxes):
        try:
            aligned = self.detector.extract(rgb_image, boxes, None)
            if aligned is None:
                return None
            if isinstance(aligned, torch.Tensor):
                return aligned
            return torch.from_numpy(aligned)
        except Exception:
            return None

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
