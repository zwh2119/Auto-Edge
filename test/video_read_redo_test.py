import time

import cv2


def main():
    url = 'rtsp://192.168.1.4/video0'
    cap = cv2.VideoCapture(url)

    while True:
        ret, frame = cap.read()

        while not ret:
            print('no signal of video source..')
            time.sleep(1)
            cap = cv2.VideoCapture(url)
            ret, frame = cap.read()

        print('get a frame form source')
        print('fps:', cap.get(cv2.CAP_PROP_FPS))


def skip_frame_test():
    url = 'rtsp://192.168.1.4/video0'
    cap = cv2.VideoCapture(url)

    while True:
        ret, frame = cap.read()

        while not ret:
            print('no signal of video source..')
            time.sleep(1)
            cap = cv2.VideoCapture(url)
            ret, frame = cap.read()

        print('get a frame form source')


if __name__ == '__main__':
    main()
