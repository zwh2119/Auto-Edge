import argparse
import ctypes
import json
import os.path
import time

import numpy as np

import pycuda.autoinit
import pycuda.driver as cuda
import tensorrt as trt

import cv2
from tqdm import tqdm
import sys

sys.path.append('..')
from car_detection import car_detection


def calculate_iou(boxA, boxB):
    # Determine the coordinates of the intersection rectangle
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    # Compute the area of intersection
    interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)

    # Compute the area of both the prediction and ground-truth rectangles
    boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
    boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)

    # Compute the intersection over union
    iou = interArea / float(boxAArea + boxBArea - interArea)

    return iou


def compute_ap(recalls, precisions):
    # Compute AP by numerical integration of the precision-recall curve
    recalls = np.concatenate(([0.0], recalls, [1.0]))
    precisions = np.concatenate(([0.0], precisions, [0.0]))
    for i in range(precisions.size - 1, 0, -1):
        precisions[i - 1] = np.maximum(precisions[i - 1], precisions[i])
    indices = np.where(recalls[1:] != recalls[:-1])[0] + 1
    ap = np.sum((recalls[indices] - recalls[indices - 1]) * precisions[indices])
    return ap


def calculate_map(predictions, ground_truths, iou_threshold=0.5):
    """
    predictions: list of dicts with keys {'bbox': [x1, y1, x2, y2], 'prob': confidence, 'class': class_id}
    ground_truths: list of dicts with keys {'bbox': [x1, y1, x2, y2], 'class': class_id}
    """
    aps = []
    for class_id in set([gt['class'] for gt in ground_truths]):
        # Filter predictions and ground truths by class
        preds = [p for p in predictions if p['class'] == class_id]
        gts = [gt for gt in ground_truths if gt['class'] == class_id]

        # Sort predictions by confidence
        preds.sort(key=lambda x: x['prob'], reverse=True)

        tp = np.zeros(len(preds))
        fp = np.zeros(len(preds))
        used_gts = set()

        for i, pred in enumerate(preds):
            max_iou = 0
            max_gt_idx = -1
            for j, gt in enumerate(gts):
                iou = calculate_iou(pred['bbox'], gt['bbox'])
                if iou > max_iou and j not in used_gts:
                    max_iou = iou
                    max_gt_idx = j

            if max_iou >= iou_threshold:
                tp[i] = 1
                used_gts.add(max_gt_idx)
            else:
                fp[i] = 1

        # Calculate precision and recall
        fp_cumsum = np.cumsum(fp)
        tp_cumsum = np.cumsum(tp)
        recalls = tp_cumsum / len(gts)
        precisions = tp_cumsum / (tp_cumsum + fp_cumsum)

        ap = compute_ap(recalls, precisions)
        aps.append(ap)

    # Mean AP
    mAP = np.mean(aps)
    return mAP


def warm_up(model, base_dir, gt_path, warm_number):
    with open(gt_path, 'r') as gt_f_:
        gt_ = gt_f_.readlines()
    count = 0
    for i_ in gt_:
        count += 1
        if count >= warm_number:
            break
        info_ = i_.split(' ')
        pic_path_ = os.path.join(base_dir, info_[0])
        frame_ = cv2.imread(pic_path_)
        model([frame_])


if __name__ == '__main__':

    resolution_dict = {
        "HVGA_360p(4:3)": (480, 360),
        "nHD_360p(16:9)": (640, 360),

        "VGA_480p(4:3)": (640, 480),

        "SVGA_600p(4:3)": (800, 600),

        "qHD_540p(16:9)": (960, 540),

        "DVCPRO-HD_720p(4:3)": (960, 720),  # 691200
        "HD_720p(16:9)": (1280, 720),  # 921600
        "WallpaperHD_720p(18:9)": (1440, 720),  # 1036800

        "WXGA_800p(16:10)": (1280, 800),  # 1024000
        "QuadVGA_960p(4:3)": (1280, 960),  # 1228800
        "WXGA+_900p(16:10)": (1440, 900),  # 1296000
        "FWXGA+_960p(3:2)": (1440, 960),  # 1382400
        "HD+_900p(16:9)": (1600, 900),  # 1440000

        "DVCPRO-HD_1080p(16:9)": (1440, 1080),  # 1555200
        "FHD_1080p(16:9)": (1920, 1080)  # 2073600
    }

    video_dir = '/data/edge_computing_dataset/UA-DETRAC/Insight-MVT_Annotation_Train'
    model_dir = '../batch_test'
    batch = 1
    save_file = 'resolution_acc_delay_notrt.log'

    gt_file = '/data/edge_computing_dataset/UA-DETRAC/train_gt.txt'

    gap_cnt = 60

    if os.path.exists(save_file):
        os.remove(save_file)

    estimator = car_detection.CarDetection({
        'weights': 'yolov5s.pt',
        'device': 'cuda:0'
    })

    # warm_up(estimator, video_dir, gt_file, 100)

    with open(gt_file, 'r') as gt_f:
        gt = gt_f.readlines()

    avg_time = []
    avg_acc = []

    all_time_dict = {}
    all_acc_dict = {}

    for resolution in resolution_dict:

        time_buffer = []
        acc_buffer = []

        print('############################################')
        print(f'testing for resolution {resolution}..')

        new_length = resolution_dict[resolution][0]
        new_height = resolution_dict[resolution][1]

        cnt = 0
        for i in tqdm(gt):
            if cnt % gap_cnt != 0:
                cnt += 1
                continue

            info = i.split(' ')
            pic_path = os.path.join(video_dir, info[0])
            frame = cv2.imread(pic_path)
            raw_length = frame.shape[1]
            raw_height = frame.shape[0]

            frame = cv2.resize(frame, resolution_dict[resolution])

            start_time = time.time()
            results = estimator([frame])
            end_time = time.time()

            result = []
            for one_res, one_prob in zip(results['result'][0], results['probs'][0]):
                result.append({'bbox': one_res, 'prob': one_prob, 'class': 1})

            process_time = (end_time - start_time) * 1000
            time_buffer.append(process_time)

            bbox_gt = [float(b) for b in info[1:]]
            boxes_gt = np.array(bbox_gt, dtype=np.float32).reshape(-1, 4)
            frame_gt = []
            for box in boxes_gt.tolist():
                box[0] *= new_length / raw_length
                box[1] *= new_height / raw_height
                box[2] *= new_length / raw_length
                box[3] *= new_height / raw_height
                frame_gt.append({'bbox': box, 'class': 1})

            acc = calculate_map(result, frame_gt)
            acc_buffer.append(acc)

            # print(f'{resolution=}    acc:{acc:.2f}    delay:{process_time:.2f}ms')
            cnt += 1

        all_time_dict[resolution] = time_buffer
        all_acc_dict[resolution] = acc_buffer
        avg_time.append(np.mean(time_buffer))
        avg_acc.append(np.mean(acc_buffer))

    print('******************************************')
    print('*************final result*****************')
    for resolution, frame_time, frame_acc in zip(resolution_dict, avg_time, avg_acc):
        print(f'resolution:{resolution}  time:{frame_time:.2f}ms   acc: {frame_acc:.2f}')
    print('******************************************')
    print('******************************************')

    with open(save_file, 'w') as f:
        json.dump({'time': all_time_dict, 'acc': all_acc_dict}, f)
