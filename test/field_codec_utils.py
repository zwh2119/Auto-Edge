import cv2
import numpy as np

def encode_image_tobytes(img_rgb):
    img_bytes = cv2.imencode('.jpg', img_rgb)[1].tobytes()

    return img_bytes

def encode_image(img_rgb):
    img_bytestr = str(cv2.imencode('.jpg', img_rgb)[1].tobytes())

    return img_bytestr

def decode_image(img_bytes):
    img_jpg = np.frombuffer(eval(img_bytes), dtype=np.uint8)
    img_rgb = np.array(cv2.imdecode(img_jpg, cv2.IMREAD_UNCHANGED))

    return img_rgb
