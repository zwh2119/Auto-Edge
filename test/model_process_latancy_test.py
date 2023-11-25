import time

import cv2
import pickle
import sys
sys.path.append('..')
from car_detection.car_detection_tmp import CarDetection
import numpy as np




def main():
    estimator = CarDetection({
        'weights': 'yolov5s.pt',
        'device': 'cuda:0'
    })

    cap = cv2.VideoCapture('traffic0.mp4')

    tmp_frame_buffer = []
    cnt = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        tmp_frame_buffer.append(frame)

        if len(tmp_frame_buffer) < 1:
            continue
        else:
            start = time.time()
            result = estimator(tmp_frame_buffer)
            end = time.time()
            print(f'process time: {end-start}s')
            tmp_frame_buffer = []


if __name__ == '__main__':
    main()
