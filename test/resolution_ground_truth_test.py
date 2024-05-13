import cv2
import matplotlib.pyplot as plt
import matplotlib.image as pimg
import numpy as np


def plot_bbox(img, boxes):
    plt.figure(figsize=(10, 10))
    plt.imshow(img)

    for b in boxes:
        rect = plt.Rectangle((b[0], b[1]), b[2] - b[0],
                             b[3] - b[1], fill=False,
                             edgecolor=(0, 1, 0),
                             linewidth=1)
        plt.gca().add_patch(rect)
    plt.show()


def main():
    with open('./train_gt.txt', 'r') as f:
        gt = f.readlines()

    base_dir = './DETRAC-train-data/Insight-MVT_Annotation_Train/'

    i = gt[0]
    info = i.split(' ')

    img = pimg.imread(base_dir + info[0])
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
