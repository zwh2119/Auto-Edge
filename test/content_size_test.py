"""
compare video size with frame bounding box

"""
import time

import cv2
import pickle
from car_detection.car_detection_tmp import CarDetection
import numpy as np
import sys


def compress_video(frames, fourcc, generator_id):
    fourcc = cv2.VideoWriter_fourcc(*fourcc)
    height, width, _ = frames[0].shape
    buffer_path = f'temp_{generator_id}.mp4'
    out = cv2.VideoWriter(buffer_path, fourcc, 30, (width, height))
    for frame in frames:
        out.write(frame)
    out.release()
    return buffer_path





def main():
    buffer_size = 8

    estimator = CarDetection({
        'weights': 'yolov5s.pt',
        'device': 'cpu'
    })

    cap = cv2.VideoCapture('traffic0.mp4')

    tmp_frame_buffer = []
    cnt = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        tmp_frame_buffer.append(frame)
        cv2.imwrite(f'pic.jpg', frame)
        print('frame size:', frame.__sizeof__())
        cnt+=1
        # print('get a frame..')
        if cnt % 4 != 0:
            continue
        if len(tmp_frame_buffer) < buffer_size:
            continue
        else:
            start = time.time()
            buffer_path = compress_video(tmp_frame_buffer, 'mp4v', 0)
            end = time.time()
            print(f'compress time:{end-start}')
            print('video path:', buffer_path)
            result = estimator(tmp_frame_buffer)
            frame_result = result['result']
            bbox_frames = []
            for i in range(len(tmp_frame_buffer)):
                bboxes = frame_result[i]
                frame = tmp_frame_buffer[i]
                frame = np.array(frame)
                # print(frame.shape)
                bbox_frame = []
                for bbox in bboxes:
                    # print(bbox[0])
                    tmp_bbox = frame[int(bbox[1]):int(bbox[3]), int(bbox[0]):int(bbox[2])]
                    # bbox_frame.append(cv2.imencode('.jpg', tmp_bbox)[1])
                    bbox_frame.append(tmp_bbox)

                bbox_frames.append(bbox_frame)
            with open('tmp_bbox_single_1_', 'wb') as file:
                pickle.dump(frame_result, file)
            with open('tmp_bbox_1_', 'wb') as file:
                pickle.dump(bbox_frames, file)

            break


if __name__ == '__main__':
    main()
