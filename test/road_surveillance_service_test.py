import sys
import os

sys.path.append('/home/hx/zwh/Auto-Edge-rebuild')
print(sys.path)

import cv2
import numpy as np

from core.lib.common import Context
from core.lib.common import ClassFactory, ClassType
from applications import *


def road_surveillance():
    video_dir = '/data/edge_computing_dataset/UA-DETRAC/Insight-MVT_Annotation_Train'
    gt_file = '/data/edge_computing_dataset/UA-DETRAC/train_gt.txt'

    with open(gt_file, 'r') as gt_f:
        gt_file = gt_f.readlines()
        gt_file = gt_file[:16]

    weights = '/home/hx/zwh/Auto-Edge/batch_test/yolov5s_batch1.engine'
    plugin = '/home/hx/zwh/Auto-Edge/batch_test/libbatch1plugins.so'
    processor = ClassFactory.get_cls(ClassType.PRO_DETECTOR,
                                     'car_detection')(weights, plugin)

    frame_list = []
    for i in gt_file:
        info = i.split(' ')

        pic_path = os.path.join(video_dir, info[0])
        frame = cv2.imread(pic_path)
        frame_list.append(frame)

    output = processor(frame_list)



if __name__ == '__main__':
    road_surveillance()
