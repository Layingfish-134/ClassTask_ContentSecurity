import cv2
import numpy as np
import base64
import os


def base64_to_image(image_base64):
    try:
        if ',' in image_base64:
            image_base64 = image_base64.split(',', 1)[1]

        image_data = base64.b64decode(image_base64)
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return image
    except Exception:
        return None


def image_to_base64(image, format='.jpg'):
    try:
        _, buffer = cv2.imencode(format, image)
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        return f'data:image/jpeg;base64,{image_base64}'
    except Exception:
        return None


def save_image(image_base64, filepath):
    if ',' in image_base64:
        image_base64 = image_base64.split(',', 1)[1]

    image_data = base64.b64decode(image_base64)

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'wb') as f:
        f.write(image_data)


def resize_image(image, target_size=(160, 160)):
    try:
        return cv2.resize(image, target_size)
    except Exception:
        return image


def decode_image_bytes(image_bytes):
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    except Exception:
        return None
