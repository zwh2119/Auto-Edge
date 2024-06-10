import os
import pickle
import shutil
import sys
import cv2

from car_detection_trt_for_test import CarDetection
from pympler import asizeof


def get_file_size(file_path: str):
    return os.path.getsize(file_path)


def segment_frame_bbox(frame, bbox):
    frame_bbox_list = []
    for index, (x_min, y_min, x_max, y_max) in enumerate(bbox):
        print(bbox[index])
        frame_bbox = frame[int(y_min):int(y_max), int(x_min):int(x_max)]
        frame_bbox_list.append(frame_bbox)
    return frame_bbox_list


def get_object_file_size(obj):
    temp_path = 'temp_file'
    with open(temp_path, 'wb') as file:
        pickle.dump(obj, file)
    obj_size = get_file_size(temp_path)
    os.remove(temp_path)
    # obj_size = asizeof.asizeof(obj)

    return obj_size


def compress_frames_to_video(frame_list):
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    height, width, _ = frame_list[0].shape
    buffer_path = 'temp_video.mp4'
    out = cv2.VideoWriter(buffer_path, fourcc, 30, (width, height))
    for frame in frame_list:
        out.write(frame)
    out.release()

    output_size = get_file_size(buffer_path)
    os.remove(buffer_path)

    return output_size


def plot_bbox(frame, boxes):

    boxes.sort(key=lambda x: x[0])
    for index, (x_min, y_min, x_max, y_max) in enumerate(boxes):

        cv2.rectangle(frame, (int(x_min), int(y_min)), (int(x_max), int(y_max)),(0,255,0), 2)

    return frame


def frame_bbox_segment_test():
    save_dir = 'frame_bbox_segmentation'
    if os.path.exists(save_dir):
        shutil.rmtree(save_dir)
    os.mkdir(save_dir)

    weights = '/home/hx/zwh/Auto-Edge/batch_test/yolov5s_batch1.engine'
    plugin = '/home/hx/zwh/Auto-Edge/batch_test/libbatch1plugins.so'
    processor = CarDetection({'weights': weights, 'plugin_library': plugin})

    video_path = 'traffic1.mp4'
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, 832)
    success, frame = cap.read()
    assert success, 'video read fail!'
    cv2.imwrite(os.path.join(save_dir, 'frame.png'), frame)

    output = processor([frame])
    bbox = output['result'][0]
    frame_plot = plot_bbox(frame.copy(), bbox)
    cv2.imwrite(os.path.join(save_dir, 'frame_result.png'), frame_plot)

    frame_bbox_list = segment_frame_bbox(frame.copy(), bbox)
    for index, frame_bbox in enumerate(frame_bbox_list):
        cv2.imwrite(os.path.join(save_dir, f'fig_{index}.png'), frame_bbox)


def different_num_test():
    weights = '/home/hx/zwh/Auto-Edge/batch_test/yolov5s_batch1.engine'
    plugin = '/home/hx/zwh/Auto-Edge/batch_test/libbatch1plugins.so'
    processor = CarDetection({'weights': weights, 'plugin_library': plugin})

    video_path = 'traffic1.mp4'
    cap = cv2.VideoCapture(video_path)

    frame_best = None
    bbox_best = None

    success = True
    while success:
        success, frame = cap.read()
        if not success:
            break

        output = processor([frame])
        bbox = output['result'][0]
        if not bbox_best or len(bbox) > len(bbox_best):
            frame_best = frame
            bbox_best = bbox
            print(f'update best: obj_num {len(bbox)} / no.{cap.get(cv2.CAP_PROP_POS_FRAMES)}')


def different_package_size_test():
    weights = '/home/hx/zwh/Auto-Edge/batch_test/yolov5s_batch1.engine'
    plugin = '/home/hx/zwh/Auto-Edge/batch_test/libbatch1plugins.so'
    processor = CarDetection({'weights': weights, 'plugin_library': plugin})

    video_path = 'traffic1.mp4'
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, 832)

    package_sizes = [2, 4, 6, 8, 10, 12, 14, 16]

    frame_list = []
    frame_bbox_list = []
    bbox_list = []

    compress_size = []
    segment_size = []

    for package_size in package_sizes:

        success = True
        while success:
            success, frame = cap.read()
            if not success:
                assert None, 'video read failed!'

            frame_list.append(frame.copy())
            output = processor([frame])
            bbox = output['result'][0]
            frame_bbox_list.append(segment_frame_bbox(frame.copy(), bbox))
            bbox_list.append(bbox)

            if len(frame_list) == package_size:
                compress_file_size = compress_frames_to_video(frame_list)
                compress_bbox_size = get_object_file_size(bbox_list)
                segment_file_size = get_object_file_size(frame_bbox_list)
                compress_size.append(compress_file_size + compress_bbox_size)
                segment_size.append(segment_file_size)
                print(f'[package size: {package_size}] '
                      f'compress size:{compress_size[-1]}({compress_file_size / compress_size[-1]}) '
                      f' /  segmentation size: {segment_size[-1]}')

                frame_list = []
                frame_bbox_list = []
                bbox_list = []
                break

    print('--------------------------------')
    print(f'compress size: {compress_size}')
    print(f'segment size: {segment_size}')


if __name__ == '__main__':
    # different_package_size_test()
    # different_num_test()
    frame_bbox_segment_test()
