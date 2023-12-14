import json
import os
import shutil
import time
import  random

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
    write_dir = 'output'
    if os.path.exists(write_dir):
        shutil.rmtree(write_dir)
    os.mkdir(write_dir)

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
        # frame = cv2.resize(frame, (640,640))

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

            response = requests.post(service_address,
                          data={'data': json.dumps(None)},
                          files={'file': (f'tmp.mp4',
                                          open(compressed_video_pth, 'rb'),
                                          'video/mp4')})
            data = response.json()['result']
            for i in range(len(temp_frame_buffer)):
                boxes = data[i]
                frame = temp_frame_buffer[i]
                for box in boxes:
                    plot_one_box(box, frame, label='')
                cv2.imwrite(os.path.join(write_dir, f'output_{i}.png'), frame)

            cur_id += 1
            temp_frame_buffer = []
            os.remove(compressed_video_pth)

            time.sleep(2)
            break

def plot_one_box(x, img, color=None, label=None, line_thickness=None):
    """
    description: Plots one bounding box on image img,
                 this function comes from YoLov5 project.
    param:
        x:      a box likes [x1,y1,x2,y2]
        img:    a opencv image object
        color:  color to draw rectangle, such as (0,255,0)
        label:  str
        line_thickness: int
    return:
        no return

    """
    tl = (
        line_thickness or round(0.002 * (img.shape[0] + img.shape[1]) / 2) + 1
    )  # line/font thickness
    color = color or [random.randint(0, 255) for _ in range(3)]
    c1, c2 = (int(x[0]), int(x[1])), (int(x[2]), int(x[3]))
    cv2.rectangle(img, c1, c2, color, thickness=tl, lineType=cv2.LINE_AA)
    if label:
        tf = max(tl - 1, 1)  # font thickness
        t_size = cv2.getTextSize(label, 0, fontScale=tl / 3, thickness=tf)[0]
        c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3
        cv2.rectangle(img, c1, c2, color, -1, cv2.LINE_AA)  # filled
        cv2.putText(
            img,
            label,
            (c1[0], c1[1] - 2),
            0,
            tl / 3,
            [225, 255, 255],
            thickness=tf,
            lineType=cv2.LINE_AA,
        )


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
