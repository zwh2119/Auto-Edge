import os
import shutil

import cv2

from car_detection_trt_for_test import CarDetection



def plot_bbox(frame, boxes):
    colors = [
        (109, 162,199),
        (121, 112,242),
        (187,151, 39),
        (84, 179, 69),

    ]
    boxes.sort(key=lambda x:x[0])
    for index, (x_min, y_min, x_max, y_max) in enumerate(boxes):
        print(boxes[index])
        if index < len(boxes) * 0.1:
            color = colors[0]
        elif index < len(boxes) * 0.3:
            color = colors[1]
        elif index < len(boxes) * 0.6:
            color = colors[2]
        else:
            color = colors[3]
        cv2.rectangle(frame, (int(x_min), int(y_min)), (int(x_max), int(y_max)), color, 2)

    cv2.imwrite('car_result.png', frame)


def inference(frame):
    weights = '/home/hx/zwh/Auto-Edge/batch_test/yolov5s_batch1.engine'
    plugin = '/home/hx/zwh/Auto-Edge/batch_test/libbatch1plugins.so'
    processor = CarDetection({'weights': weights, 'plugin_library': plugin})
    output = processor([frame])
    boxes = output['result'][0]
    return boxes


def main():
    image_path = '/data/edge_computing_dataset/UA-DETRAC/Insight-MVT_Annotation_Train/MVI_41073/img00707.jpg'
    shutil.copyfile(image_path, 'car_raw.png')

    img = cv2.imread(image_path)
    boxes = inference(img)

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
