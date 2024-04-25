from typing import List

import cv2
import numpy as np


class CarTracking:
    def __init__(self):
        pass

    def __call__(self, prev_detection_frame: np.ndarray, bbox: List, tracking_frame_list: List[np.ndarray]):
        if not tracking_frame_list:
            return []

        # Bounding boxes are assumed to be in xywh format directly.
        grey_prev_frame = cv2.cvtColor(prev_detection_frame, cv2.COLOR_BGR2GRAY)
        key_points = self.select_key_points(bbox, grey_prev_frame, max_corners=max(len(bbox) * 5, 50))

        result = []
        for present_frame in tracking_frame_list:
            grey_present_frame = cv2.cvtColor(present_frame, cv2.COLOR_BGR2GRAY)
            new_points, status, error = cv2.calcOpticalFlowPyrLK(grey_prev_frame, grey_present_frame, key_points, None)

            if len(key_points) > 0 and len(new_points) > 0:
                bbox = self.update_bounding_boxes(bbox, key_points, new_points, status)
                result.append(bbox.copy())  # Append the updated boxes in the same format
            else:
                result.append([])

            grey_prev_frame = grey_present_frame.copy()
            key_points = new_points[status == 1].reshape(-1, 1, 2)

        return result

    @staticmethod
    def select_key_points(bounding_boxes, gray_image, max_corners=40, quality_level=0.01, min_distance=20):
        points = []
        for (x, y, w, h) in bounding_boxes:
            roi = gray_image[y:y + h, x:x + w]
            corners = cv2.goodFeaturesToTrack(roi, maxCorners=max_corners, qualityLevel=quality_level,
                                              minDistance=min_distance)
            if corners is not None:
                corners += np.array([x, y], dtype=np.float32)
                points.extend(corners.tolist())

        return np.array(points, dtype=np.float32) if points else np.empty((0, 1, 2), dtype=np.float32)

    @staticmethod
    def update_bounding_boxes(bounding_boxes, old_points, new_points, status):
        updated_boxes = []
        point_movements = new_points - old_points
        for box in bounding_boxes:
            x, y, w, h = box
            points_in_box = ((old_points[:, 0, 0] >= x) & (old_points[:, 0, 0] < x + w) &
                             (old_points[:, 0, 1] >= y) & (old_points[:, 0, 1] < y + h)).reshape(-1)
            valid_points_in_box = points_in_box & (status.flatten() == 1)
            if not np.any(valid_points_in_box):
                updated_boxes.append(box)
                continue
            average_movement = np.mean(point_movements[valid_points_in_box], axis=0).reshape(-1)
            dx, dy = average_movement[0], average_movement[1]
            updated_box = (x + int(dx), y + int(dy), w, h)
            updated_boxes.append(updated_box)
        return updated_boxes
