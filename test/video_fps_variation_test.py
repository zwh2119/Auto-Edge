import time

import cv2


def test_video_fps(url):
    while True:
        cap = cv2.VideoCapture(url)
        fps = cap.get(cv2.CAP_PROP_FPS)
        print(f'fps: {fps}')
        time.sleep(2)


if __name__ == '__main__':
    test_video_fps('rtsp://192.168.1.91/video0')
