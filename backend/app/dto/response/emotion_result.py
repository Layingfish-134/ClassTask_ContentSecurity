class EmotionResult:
    def __init__(self, emotion='neutral', confidence=0.0):
        self.emotion = emotion
        self.confidence = confidence

    def to_dict(self):
        return {
            'emotion': self.emotion,
            'emotion_confidence': round(self.confidence, 2)
        }
