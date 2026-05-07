import cv2
import numpy as np
import os
import torch

try:
    from torchvision import models, transforms
    TORCHVISION_AVAILABLE = True
except ImportError:
    TORCHVISION_AVAILABLE = False

EMOTION_LABELS = ['happy', 'sad', 'surprised', 'angry', 'neutral']


class EmotionClassifier:
    def __init__(self):
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.transform = None
        self._init_model()

    def _init_model(self):
        if TORCHVISION_AVAILABLE:
            self.model = models.resnet50(weights=None)
            self.model.fc = torch.nn.Linear(self.model.fc.in_features, 5)

            model_path = os.getenv('EMOTION_MODEL_PATH', 'models/resnet/')
            model_file = os.path.join(model_path, 'emotion_resnet.pth')

            if os.path.exists(model_file):
                try:
                    state_dict = torch.load(model_file, map_location=self.device)
                    self.model.load_state_dict(state_dict)
                    self.model = self.model.to(self.device)
                    self.model.eval()
                except Exception:
                    self.model = None
            else:
                self.model = None

            self.transform = transforms.Compose([
                transforms.ToPILImage(),
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                     std=[0.229, 0.224, 0.225])
            ])

    def classify_emotion(self, face_image):
        if isinstance(face_image, bytes):
            nparr = np.frombuffer(face_image, np.uint8)
            face_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if face_image is None:
            from app.dto.response.emotion_result import EmotionResult
            return EmotionResult(emotion='neutral', confidence=0.0)

        if self.model is not None and self.transform is not None:
            return self._classify_deep(face_image)
        else:
            return self._classify_simple(face_image)

    def _classify_deep(self, face_image):
        from app.dto.response.emotion_result import EmotionResult

        try:
            face_resized = cv2.resize(face_image, (224, 224))
            face_rgb = cv2.cvtColor(face_resized, cv2.COLOR_BGR2RGB)
            face_tensor = self.transform(face_rgb).unsqueeze(0).to(self.device)

            with torch.no_grad():
                output = self.model(face_tensor)
                probabilities = torch.softmax(output, dim=1)
                confidence, predicted = torch.max(probabilities, 1)

            emotion_idx = predicted.item()
            conf = confidence.item() * 100

            return EmotionResult(
                emotion=EMOTION_LABELS[emotion_idx],
                confidence=conf
            )
        except Exception:
            return self._classify_simple(face_image)

    def _classify_simple(self, face_image):
        from app.dto.response.emotion_result import EmotionResult

        try:
            gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, (48, 48))

            mean_val = np.mean(gray)
            std_val = np.std(gray)

            if std_val < 30:
                emotion = 'neutral'
                confidence = 60.0
            elif mean_val > 150:
                emotion = 'happy'
                confidence = 55.0
            elif mean_val < 80:
                emotion = 'sad'
                confidence = 50.0
            else:
                emotion = 'neutral'
                confidence = 50.0

            return EmotionResult(emotion=emotion, confidence=confidence)
        except Exception:
            return EmotionResult(emotion='neutral', confidence=0.0)

    def classify_emotion_from_base64(self, image_base64):
        from app.utils.image_utils import base64_to_image
        image = base64_to_image(image_base64)
        if image is None:
            from app.dto.response.emotion_result import EmotionResult
            return EmotionResult(emotion='neutral', confidence=0.0)
        return self.classify_emotion(image)
