import base64
import json

import cv2
import os

import requests


def compress_video(frames, fourcc, generator_id):
    fourcc = cv2.VideoWriter_fourcc(*fourcc)
    height, width, _ = frames[0].shape
    buffer_path = f'temp_{generator_id}.mp4'
    out = cv2.VideoWriter(buffer_path, fourcc, 30, (width, height))
    for frame in frames:
        out.write(frame)
    out.release()
    with open(buffer_path, 'rb') as f:
        compressed_video = f.read()
    # delete the temporary file
    os.remove(buffer_path)
    base64_frame = base64.b64encode(compressed_video)
    return base64_frame


def compress_video_second(frames, fourcc, generator_id):
    fourcc = cv2.VideoWriter_fourcc(*fourcc)
    height, width, _ = frames[0].shape
    buffer_path = f'temp_{generator_id}.mp4'
    out = cv2.VideoWriter(buffer_path, fourcc, 30, (width, height))
    for frame in frames:
        out.write(frame)
    out.release()
    return buffer_path


def decompress_video(encode_frame):
    frames = base64.b64decode(encode_frame)
    return frames


def main():
    cap = cv2.VideoCapture('traffic0.mp4')

    tmp_frame_buffer = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        tmp_frame_buffer.append(frame)
        print('get a frame..')
        if len(tmp_frame_buffer) < 8:
            continue
        else:
            compress_frames = compress_video(tmp_frame_buffer, 'mp4v', 0)
            print('compress successfully')
            frames = decompress_video(compress_frames)
            print('decompress successfully')


def main_second():
    cap = cv2.VideoCapture('traffic0.mp4')

    tmp_frame_buffer = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        tmp_frame_buffer.append(frame)
        print('get a frame..')
        if len(tmp_frame_buffer) < 8:
            continue
        else:
            data = {'name': 'file'}
            compress_frames_path = compress_video_second(tmp_frame_buffer, 'mp4v', 0)
            files = {'file': ('file_name.mp4', '', 'video/mp4')}
            response = requests.post(url='http://127.0.0.1:1234/test', data={'data': json.dumps(data)}, files=files)
            print(response.json())
            break


if __name__ == '__main__':
    main_second()
