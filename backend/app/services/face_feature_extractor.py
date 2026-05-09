import cv2
import numpy as np
import os

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False


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


ARCFACE_DST = np.array([
    [38.2946, 51.6963],
    [73.5318, 51.5014],
    [56.0252, 71.7366],
    [41.5493, 92.3655],
    [70.7299, 92.2041],
], dtype=np.float32)


class SCRFDDetector:
    def __init__(self, model_path):
        self.session = ort.InferenceSession(
            model_path,
            providers=['CPUExecutionProvider']
        )
        self.input_size = (640, 640)
        self._feat_stride_fpn = [8, 16, 32]
        self.fmc = 3
        self._num_anchors = 2
        self.use_kps = len(self.session.get_outputs()) == 9
        self.input_name = self.session.get_inputs()[0].name
        self._anchors_cache = {}

    def detect(self, img, threshold=0.5, nms_thresh=0.4):
        input_size = self.input_size
        im_ratio = float(img.shape[0]) / img.shape[1]
        model_ratio = float(input_size[1]) / float(input_size[0])

        if im_ratio > model_ratio:
            new_height = input_size[1]
            new_width = int(new_height / im_ratio)
        else:
            new_width = input_size[0]
            new_height = int(new_width * im_ratio)

        det_scale = float(new_height) / img.shape[0]
        resized_img = cv2.resize(img, (new_width, new_height))
        det_img = np.zeros((input_size[1], input_size[0], 3), dtype=np.uint8)
        det_img[:new_height, :new_width, :] = resized_img

        blob = cv2.dnn.blobFromImage(
            det_img, 1.0 / 128, input_size,
            (127.5, 127.5, 127.5), swapRB=True
        )
        net_outs = self.session.run(None, {self.input_name: blob})

        input_height = blob.shape[2]
        input_width = blob.shape[3]

        scores_list = []
        bboxes_list = []
        kpss_list = []

        for idx, stride in enumerate(self._feat_stride_fpn):
            scores = net_outs[idx].flatten()
            bbox_preds = net_outs[idx + self.fmc] * stride

            if self.use_kps:
                kps_preds = net_outs[idx + self.fmc * 2] * stride

            height = input_height // stride
            width = input_width // stride

            key = (height, width, stride)
            if key not in self._anchors_cache:
                self._anchors_cache[key] = self._generate_anchors(
                    height, width, stride
                )
            anchors = self._anchors_cache[key]

            bbox_preds = bbox_preds.reshape(-1, 4)
            pos_inds = np.where(scores >= threshold)[0]

            if len(pos_inds) == 0:
                continue

            bboxes = self._distance2bbox(anchors, bbox_preds)
            bboxes = bboxes * det_scale
            scores_list.append(scores[pos_inds])
            bboxes_list.append(bboxes[pos_inds])

            if self.use_kps:
                kps_preds = kps_preds.reshape(-1, 10)
                kpss = self._distance2kps(anchors, kps_preds)
                kpss = kpss * det_scale
                kpss_list.append(kpss[pos_inds])

        if len(scores_list) == 0:
            return []

        scores = np.concatenate(scores_list)
        bboxes = np.concatenate(bboxes_list)
        kpss = np.concatenate(kpss_list) if self.use_kps else None

        keep = self._nms(bboxes, scores, nms_thresh)

        results = []
        for i in keep:
            result = {
                'box': bboxes[i].astype(int).tolist(),
                'confidence': float(scores[i]),
            }
            if kpss is not None:
                result['keypoints'] = kpss[i].reshape(5, 2).tolist()
            results.append(result)

        return results

    def _generate_anchors(self, height, width, stride):
        anchors = []
        for h in range(height):
            for w in range(width):
                for _ in range(self._num_anchors):
                    cx = (w + 0.5) * stride
                    cy = (h + 0.5) * stride
                    anchors.append([cx, cy])
        return np.array(anchors, dtype=np.float32)

    @staticmethod
    def _distance2bbox(points, distance):
        x1 = points[:, 0] - distance[:, 0]
        y1 = points[:, 1] - distance[:, 1]
        x2 = points[:, 0] + distance[:, 2]
        y2 = points[:, 1] + distance[:, 3]
        return np.stack([x1, y1, x2, y2], axis=-1)

    @staticmethod
    def _distance2kps(points, distance):
        preds = []
        for i in range(0, distance.shape[1], 2):
            px = points[:, 0] + distance[:, i]
            py = points[:, 1] + distance[:, i + 1]
            preds.append(px)
            preds.append(py)
        return np.stack(preds, axis=-1)

    @staticmethod
    def _nms(bboxes, scores, nms_thresh):
        x1 = bboxes[:, 0]
        y1 = bboxes[:, 1]
        x2 = bboxes[:, 2]
        y2 = bboxes[:, 3]
        areas = (x2 - x1 + 1) * (y2 - y1 + 1)
        order = scores.argsort()[::-1]

        keep = []
        while order.size > 0:
            i = order[0]
            keep.append(i)

            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])

            w = np.maximum(0.0, xx2 - xx1 + 1)
            h = np.maximum(0.0, yy2 - yy1 + 1)
            inter = w * h
            ovr = inter / (areas[i] + areas[order[1:]] - inter)

            inds = np.where(ovr <= nms_thresh)[0]
            order = order[inds + 1]

        return keep


class ArcFaceExtractor:
    def __init__(self, model_path):
        self.session = ort.InferenceSession(
            model_path,
            providers=['CPUExecutionProvider']
        )
        self.input_name = self.session.get_inputs()[0].name
        self.input_size = (112, 112)

    def extract(self, image, keypoints):
        kps = np.array(keypoints, dtype=np.float32).reshape(5, 2)
        M, _ = cv2.estimateAffinePartial2D(kps, ARCFACE_DST)
        if M is None:
            return None

        aligned = cv2.warpAffine(
            image, M, self.input_size, borderValue=0.0
        )

        blob = cv2.dnn.blobFromImage(
            aligned, 1.0 / 127.5, self.input_size,
            (127.5, 127.5, 127.5), swapRB=True
        )

        net_out = self.session.run(None, {self.input_name: blob})
        embedding = net_out[0].flatten()

        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    def extract_no_align(self, face_image):
        face_resized = cv2.resize(face_image, self.input_size)
        blob = cv2.dnn.blobFromImage(
            face_resized, 1.0 / 127.5, self.input_size,
            (127.5, 127.5, 127.5), swapRB=True
        )

        net_out = self.session.run(None, {self.input_name: blob})
        embedding = net_out[0].flatten()

        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding


class FaceFeatureExtractor:
    def __init__(self):
        self.detector = None
        self.arcface = None
        self._init_models()

    def _init_models(self):
        if not ONNX_AVAILABLE:
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

        try:
            arcface_path = os.getenv(
                'FACE_RECOGNITION_MODEL_PATH', 'models/arcface/'
            )
            model_file = _find_model_file(
                arcface_path,
                'w600k_r50.onnx',
                'models/arcface/'
            )
            if os.path.exists(model_file):
                self.arcface = ArcFaceExtractor(model_file)
        except Exception:
            self.arcface = None

    def detect_face(self, image):
        if self.detector is None:
            return self._detect_face_opencv(image)

        try:
            results = self.detector.detect(
                image, threshold=0.5, nms_thresh=0.4
            )

            if not results:
                return None

            best = max(results, key=lambda r: r['confidence'])

            x1, y1, x2, y2 = best['box']
            x1, y1 = max(0, x1), max(0, y1)
            y2 = min(image.shape[0], y2)
            x2 = min(image.shape[1], x2)

            face_image = image[y1:y2, x1:x2]
            if face_image.size == 0:
                return None

            return {
                'box': (x1, y1, x2, y2),
                'confidence': best['confidence'],
                'face_image': face_image,
                'keypoints': best.get('keypoints', [])
            }
        except Exception:
            return self._detect_face_opencv(image)

    def _detect_face_opencv(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        cascade_path = (
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        face_cascade = cv2.CascadeClassifier(cascade_path)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces) == 0:
            return None

        x, y, w, h = faces[0]
        return {
            'box': (x, y, x + w, y + h),
            'confidence': 0.9,
            'face_image': image[y:y + h, x:x + w],
            'keypoints': []
        }

    def extract_feature(self, face_image, original_image=None, keypoints=None):
        if self.arcface is not None:
            if original_image is not None and keypoints:
                try:
                    return self.arcface.extract(original_image, keypoints)
                except Exception:
                    pass
            try:
                return self.arcface.extract_no_align(face_image)
            except Exception:
                pass

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

        keypoints = face_result.get('keypoints', [])
        return self.extract_feature(
            face_result['face_image'],
            original_image=image,
            keypoints=keypoints if keypoints else None
        )
