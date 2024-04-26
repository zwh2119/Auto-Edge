import cv2
import numpy as np


def plot_bbox(frame, boxes, points, path):
    for x_min, y_min, x_max, y_max in boxes:
        cv2.rectangle(frame, (int(x_min), int(y_min)), (int(x_max), int(y_max)), (0, 255, 0), 4)
    points = np.int0(points)
    for point in points:
        x, y = point.ravel()
        cv2.circle(frame, (int(x), int(y)), 1, (0, 0, 255), 3)

    cv2.imwrite(path, frame)


def extract_features():
    pic_path = '/data/edge_computing_dataset/UA-DETRAC/Insight-MVT_Annotation_Train/MVI_20011/img00001.jpg'
    frame = cv2.imread(pic_path)
    print(f'raw frame shape: {frame.shape}')
    grey_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    print(f'frame shape: {grey_frame.shape}')
    corners = cv2.goodFeaturesToTrack(grey_frame, maxCorners=0, qualityLevel=0.001, minDistance=1)
    if corners is None:
        print('None')
    else:
        for corner in corners:
            # print(corner)
            x, y = corner.ravel()
            if x > 540:
                cv2.circle(frame, (int(x), int(y)), 1, (0, 0, 255), 3)
    cv2.imwrite('test_feature.png', frame)


if __name__ == '__main__':
    extract_features()
