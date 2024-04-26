import copy
import os.path
import pickle
from typing import List

import cv2
import numpy as np


class CarTracking:
    def __init__(self):
        pass

    def __call__(self, prev_detection_frame: np.ndarray, bbox: List, tracking_frame_list: List[np.ndarray]):
        print(f'bbox length: {len(bbox)}')
        if not tracking_frame_list:
            return []

        # Bounding boxes are assumed to be in xywh format directly.
        grey_prev_frame = cv2.cvtColor(prev_detection_frame, cv2.COLOR_BGR2GRAY)
        key_points = self.select_key_points(bbox, grey_prev_frame)

        result = []
        points_list = []
        old_points = copy.deepcopy(key_points)
        for present_frame in tracking_frame_list:
            grey_present_frame = cv2.cvtColor(present_frame, cv2.COLOR_BGR2GRAY)
            new_points, status, error = cv2.calcOpticalFlowPyrLK(grey_prev_frame, grey_present_frame, key_points, None)
            print(f'point length:{len(new_points)}')
            points_list.append(new_points)

            if len(key_points) > 0 and len(new_points) > 0:
                bbox = self.update_bounding_boxes(bbox, key_points, new_points, status)
                result.append(bbox.copy())  # Append the updated boxes in the same format
            else:
                result.append([])

            grey_prev_frame = grey_present_frame.copy()
            key_points = new_points[status == 1].reshape(-1, 1, 2)

        return result, points_list, old_points

    @staticmethod
    def select_key_points(bounding_boxes, gray_image, max_corners=20, quality_level=0.0001, min_distance=1):
        points = []
        for (x1, y1, x2, y2) in bounding_boxes:
            roi = gray_image[x1:x2, y1:y2]
            print(f'*[({x1},{y1}) -> ({x2}, {y2})]')
            print(f'roi shape: {roi.shape}')
            corners = cv2.goodFeaturesToTrack(roi, maxCorners=max_corners, qualityLevel=quality_level,
                                              minDistance=min_distance)
            print(f'corners length:{len(corners) if corners is not None else None}')
            if corners is not None:
                print(corners)
                corners += np.array([x1, y1], dtype=np.float32)
                for corner in corners:
                    # print(f'  corner:{corner}')
                    x = corner[0][0]
                    y = corner[0][1]
                    if x > x2 or x < x1 or y > y2 or y < y1:
                        print(f'  corner:{corner} is out of range')
                points.extend(corners.tolist())

        return np.array(points, dtype=np.float32) if points else np.empty((0, 1, 2), dtype=np.float32)

    @staticmethod
    def update_bounding_boxes(bounding_boxes, old_points, new_points, status):
        updated_boxes = []
        point_movements = new_points - old_points
        for box in bounding_boxes:
            x1, y1, x2, y2 = box
            points_in_box = ((old_points[:, 0, 0] >= x1) & (old_points[:, 0, 0] < x2) &
                             (old_points[:, 0, 1] >= y1) & (old_points[:, 0, 1] < y2)).reshape(-1)
            valid_points_in_box = points_in_box & (status.flatten() == 1)
            if not np.any(valid_points_in_box):
                updated_boxes.append(box)
                continue
            average_movement = np.mean(point_movements[valid_points_in_box], axis=0).reshape(-1)
            dx, dy = average_movement[0], average_movement[1]
            updated_box = (x1 + int(dx), y1 + int(dy), x2 + int(dx), y2 + int(dy))
            updated_boxes.append(updated_box)
        return updated_boxes
