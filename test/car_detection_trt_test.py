import json
import os
import time

import cv2
import requests


def text2resolution(text: str):
    resolution_dict = {'1080p': (1920, 1080),
                       '720p': (1280, 720),
                       '360p': (640, 360)}

    assert text in resolution_dict
    return resolution_dict[text]


def resolution2text(resolution: tuple):
    resolution_dict = {(1920, 1080): '1080p',
                       (1280, 720): '720p',
                       (640, 360): '360p'}
    assert resolution in resolution_dict
    return resolution_dict[resolution]


def generate():
    cur_id = 0
    cnt = 0

    fps_raw = 30
    resolution_raw = '1080p'

    # default parameters
    frame_resolution = '1080p'
    frame_fourcc = 'mp4v'
    frames_per_task = 8
    fps = 30

    file_path = 'traffic1.mp4'

    service_address = 'http://114.212.81.11:9001/predict'

    fps_mode, skip_frame_interval, remain_frame_interval = get_fps_adjust_mode(fps_raw, fps)

    temp_frame_buffer = []
    cap = cv2.VideoCapture(file_path)
    while True:
        ret, frame = cap.read()

        # retry when no video signal
        while not ret:
            time.sleep(1)
            cap = cv2.VideoCapture(file_path)
            ret, frame = cap.read()

        resolution_raw = resolution2text((cap.get(cv2.CAP_PROP_FRAME_WIDTH),
                                          cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        fps_raw = cap.get(cv2.CAP_PROP_FPS)

        # adjust resolution
        frame = cv2.resize(frame, (640,640))

        # adjust fps
        cnt += 1
        if fps_mode == 'skip' and cnt % skip_frame_interval == 0:
            continue

        if fps_mode == 'remain' and cnt % remain_frame_interval != 0:
            continue

        # put frame in buffer
        temp_frame_buffer.append(frame)
        if len(temp_frame_buffer) < frames_per_task:
            continue
        else:
            # compress frames in the buffer into a short video
            compressed_video_pth = compress_frames(temp_frame_buffer, frame_fourcc)

            # start record transmit time

            # post task to local controller
            requests.post(service_address,
                          data={'data': json.dumps(None)},
                          files={'file': (f'tmp.mp4',
                                          open(compressed_video_pth, 'rb'),
                                          'video/mp4')})

            cur_id += 1
            temp_frame_buffer = []
            os.remove(compressed_video_pth)

            time.sleep(2)


def get_fps_adjust_mode(fps_raw, fps):
    fps_mode = None
    skip_frame_interval = 0
    remain_frame_interval = 0
    if fps == fps_raw:
        fps_mode = 'same'
    elif fps < fps_raw // 2:
        fps_mode = 'remain'
        remain_frame_interval = fps_raw // fps
    else:
        fps_mode = 'skip'
        skip_frame_interval = fps_raw // (fps_raw - fps)

    return fps_mode, skip_frame_interval, remain_frame_interval


def compress_frames(frames, fourcc):
    fourcc = cv2.VideoWriter_fourcc(*fourcc)
    height, width, _ = frames[0].shape
    buffer_path = f'temp.mp4'
    out = cv2.VideoWriter(buffer_path, fourcc, 30, (width, height))
    for frame in frames:
        out.write(frame)
    out.release()

    return buffer_path


if __name__ == '__main__':
    generate()
