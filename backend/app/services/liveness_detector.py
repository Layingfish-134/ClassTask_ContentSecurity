import cv2
import numpy as np
import os


class LivenessDetector:
    def __init__(self):
        self.threshold = float(os.getenv('LIVENESS_THRESHOLD', 0.75))
        self.photo_threshold = 0.4
        self.video_threshold = 0.55

    def detect_liveness(self, image_data):
        if isinstance(image_data, bytes):
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        else:
            image = image_data

        if image is None:
            return {
                'is_live': False,
                'liveness_score': 0.0,
                'spoof_type': 'unknown',
                'failure_reason': 'invalid_image'
            }

        texture_score = self._texture_analysis(image)
        color_score = self._color_analysis(image)
        fourier_score = self._fourier_analysis(image)

        combined_score = (
            texture_score * 0.4 +
            color_score * 0.3 +
            fourier_score * 0.3
        )

        spoof_type = self._classify_attack_type(combined_score, texture_score, fourier_score)

        is_live = combined_score >= self.threshold

        failure_reason = None
        if not is_live:
            if spoof_type == 'photo_attack':
                failure_reason = 'liveness_failed'
            elif spoof_type == 'video_replay':
                failure_reason = 'liveness_failed'
            elif spoof_type == 'screen_replay':
                failure_reason = 'liveness_failed'
            else:
                failure_reason = 'liveness_failed'

        return {
            'is_live': is_live,
            'liveness_score': round(float(combined_score) * 100, 2),
            'spoof_type': spoof_type if not is_live else None,
            'failure_reason': failure_reason
        }

    def detect_liveness_multi_frame(self, frames):
        if not frames or len(frames) == 0:
            return {
                'is_live': False,
                'liveness_score': 0.0,
                'spoof_type': 'unknown',
                'failure_reason': 'invalid_image'
            }

        single_results = []
        for frame_data in frames:
            result = self.detect_liveness(frame_data)
            single_results.append(result)

        scores = [r['liveness_score'] for r in single_results]
        avg_score = np.mean(scores)

        consistency_score = self._frame_consistency_check(frames)

        final_score = avg_score * 0.7 + consistency_score * 100 * 0.3

        spoof_type = None
        if final_score < self.photo_threshold * 100:
            spoof_type = 'photo_attack'
        elif final_score < self.video_threshold * 100:
            spoof_type = 'video_replay'

        is_live = final_score >= self.threshold * 100

        return {
            'is_live': is_live,
            'liveness_score': round(float(final_score), 2),
            'spoof_type': spoof_type if not is_live else None,
            'failure_reason': 'liveness_failed' if not is_live else None,
            'frame_count': len(frames),
            'single_frame_scores': scores
        }

    def _frame_consistency_check(self, frames):
        if len(frames) < 2:
            return 0.5

        images = []
        for frame_data in frames:
            if isinstance(frame_data, bytes):
                nparr = np.frombuffer(frame_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            else:
                img = frame_data
            if img is not None:
                images.append(img)

        if len(images) < 2:
            return 0.5

        diffs = []
        for i in range(len(images) - 1):
            gray1 = cv2.cvtColor(images[i], cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(images[i + 1], cv2.COLOR_BGR2GRAY)

            h = min(gray1.shape[0], gray2.shape[0])
            w = min(gray1.shape[1], gray2.shape[1])
            gray1 = cv2.resize(gray1, (w, h))
            gray2 = cv2.resize(gray2, (w, h))

            diff = cv2.absdiff(gray1, gray2)
            mean_diff = np.mean(diff) / 255.0
            diffs.append(mean_diff)

        avg_diff = np.mean(diffs) if diffs else 0

        if avg_diff < 0.01:
            return 0.2
        elif avg_diff < 0.03:
            return 0.5
        elif avg_diff < 0.10:
            return 0.9
        else:
            return 0.95

    def _classify_attack_type(self, combined_score, texture_score, fourier_score):
        if combined_score < 0.3:
            return 'photo_attack'
        elif combined_score < 0.5:
            if fourier_score < 0.4:
                return 'photo_attack'
            return 'video_replay'
        elif combined_score < self.threshold:
            if texture_score < 0.5 and fourier_score < 0.5:
                return 'screen_replay'
            return 'video_replay'
        return None

    def _texture_analysis(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        blur_score = np.var(laplacian)
        if blur_score < 50:
            return 0.2
        elif blur_score < 100:
            return 0.5
        elif blur_score < 500:
            return 0.9
        else:
            return 0.95

    def _color_analysis(self, image):
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        s = cv2.split(hsv)[1]
        v = cv2.split(hsv)[2]
        s_mean = np.mean(s)
        v_std = np.std(v)
        skin_score = 0.5
        if 20 < s_mean < 80:
            skin_score = 0.8
        if v_std > 30:
            skin_score = min(skin_score + 0.1, 1.0)
        return skin_score

    def _fourier_analysis(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, (256, 256))
        dft = cv2.dft(np.float32(gray), flags=cv2.DFT_COMPLEX_OUTPUT)
        dft_shift = np.fft.fftshift(dft)
        magnitude = cv2.magnitude(dft_shift[:, :, 0], dft_shift[:, :, 1])
        magnitude_log = np.log1p(magnitude)
        rows, cols = gray.shape
        crow, ccol = rows // 2, cols // 2
        mask = np.zeros((rows, cols), np.uint8)
        cv2.circle(mask, (ccol, crow), 30, 1, thickness=-1)
        high_freq_ratio = np.sum(magnitude_log * (1 - mask)) / (np.sum(magnitude_log) + 1e-6)
        if high_freq_ratio < 0.1:
            return 0.3
        elif high_freq_ratio < 0.2:
            return 0.6
        else:
            return 0.9

    def detect_liveness_from_base64(self, image_base64):
        from app.utils.image_utils import base64_to_image
        image = base64_to_image(image_base64)
        if image is None:
            return {
                'is_live': False,
                'liveness_score': 0.0,
                'spoof_type': 'unknown',
                'failure_reason': 'invalid_image'
            }
        return self.detect_liveness(image)

    def detect_liveness_multi_frame_base64(self, frames_base64):
        frames = []
        for frame_b64 in frames_base64:
            from app.utils.image_utils import base64_to_image
            img = base64_to_image(frame_b64)
            if img is not None:
                frames.append(img)
        return self.detect_liveness_multi_frame(frames)
