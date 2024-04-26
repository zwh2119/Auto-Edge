import shutil
import sys
import os

sys.path.append('/home/hx/zwh/Auto-Edge-rebuild')

import cv2
import numpy as np

from core.lib.common import Context
from core.lib.common import ClassFactory, ClassType
import applications


def plot_bbox(frame, boxes,points, path):
    # print(points)
    for x_min, y_min, x_max, y_max in boxes:
        cv2.rectangle(frame, (int(x_min), int(y_min)), (int(x_max), int(y_max)), (0, 255, 0), 4)
    points = np.int0(points)
    for point in points:
        x, y = point.ravel()
        cv2.circle(frame, (int(x), int(y)), 1, (0, 0, 255), 3)

    cv2.imwrite(path, frame)


def road_surveillance():
    video_dir = '/data/edge_computing_dataset/UA-DETRAC/Insight-MVT_Annotation_Train'
    gt_file = '/data/edge_computing_dataset/UA-DETRAC/train_gt.txt'

    with open(gt_file, 'r') as gt_f:
        gt_file = gt_f.readlines()
        gt_file = gt_file[500:532]

    weights = '/home/hx/zwh/Auto-Edge/batch_test/yolov5s_batch1.engine'
    plugin = '/home/hx/zwh/Auto-Edge/batch_test/libbatch1plugins.so'
    processor = ClassFactory.get_cls(ClassType.PRO_DETECTOR,
                                     'car_detection')(weights, plugin,device=3)

    frame_list = []
    cnt = 0
    for i in gt_file:
        cnt += 1
        # if cnt % 3 != 0:
        #     continue
        info = i.split(' ')

        pic_path = os.path.join(video_dir, info[0])
        frame = cv2.imread(pic_path)
        # frame = cv2.resize(frame, (480, 360))
        frame_list.append(frame)

    output = processor(frame_list)
    pic_dir = 'road_test_pics'
    if os.path.exists(pic_dir):
        shutil.rmtree(pic_dir)
    os.mkdir(pic_dir)
    for index, ((bboxes, _, _, points), frame) in enumerate(zip(output, frame_list)):
        plot_bbox(frame, bboxes, points, os.path.join(pic_dir, f'pic{index}.png'))


if __name__ == '__main__':
    road_surveillance()
