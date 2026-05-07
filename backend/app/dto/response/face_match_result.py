class FaceMatchResult:
    def __init__(self, student_id=None, name=None, class_name=None,
                 confidence=0.0, matched=False):
        self.student_id = student_id
        self.name = name
        self.class_name = class_name
        self.confidence = confidence
        self.matched = matched

    def to_dict(self):
        return {
            'student_id': self.student_id,
            'name': self.name,
            'class_name': self.class_name,
            'confidence': round(self.confidence, 2),
            'matched': self.matched
        }
