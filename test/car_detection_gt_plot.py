import os
import shutil

import cv2
import matplotlib.pyplot as plt
import matplotlib.image as pimg
import numpy as np


def plot_bbox(frame, boxes):
    for x_min, y_min, x_max, y_max in boxes:
        cv2.rectangle(frame, (int(x_min), int(y_min)), (int(x_max), int(y_max)), (0, 255, 0), 4)

    cv2.imwrite('car_result.png',frame)


def main():
    with open('/data/edge_computing_dataset/UA-DETRAC/train_gt.txt', 'r') as f:
        gt = f.readlines()

    base_dir = '/data/edge_computing_dataset/UA-DETRAC/Insight-MVT_Annotation_Train/'

    i = gt[500]
    info = i.split(' ')

    image_path = base_dir + info[0]
    shutil.copyfile(image_path, 'car_raw.png')

    img = cv2.imread(base_dir + info[0])
    bbox = [float(b) for b in info[1:]]
    boxes = np.array(bbox, dtype=np.float32).reshape(-1, 4)
    plot_bbox(img, boxes)

    img = cv2.resize(img, (1920, 1080))
    for b in boxes:
        b[0] *= 1920 / 960
        b[1] *= 1080 / 540
        b[2] *= 1920 / 960
        b[3] *= 1080 / 540
    plot_bbox(img, boxes)


if __name__ == '__main__':
    main()
