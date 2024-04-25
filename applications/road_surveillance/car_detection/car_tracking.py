import time

import cv2
import numpy as np
import torch
from typing import List


def xyxy_to_xywh(boxes_xyxy):
    if isinstance(boxes_xyxy, torch.Tensor):
        boxes_xywh = boxes_xyxy.clone()
    elif isinstance(boxes_xyxy, np.ndarray):
        boxes_xywh = boxes_xyxy.copy()
    else:
        assert None, 'error'

    boxes_xywh[:, 0] = (boxes_xyxy[:, 0] + boxes_xyxy[:, 2]) / 2.
    boxes_xywh[:, 1] = (boxes_xyxy[:, 1] + boxes_xyxy[:, 3]) / 2.
    boxes_xywh[:, 2] = boxes_xyxy[:, 2] - boxes_xyxy[:, 0]
    boxes_xywh[:, 3] = boxes_xyxy[:, 3] - boxes_xyxy[:, 1]

    return boxes_xywh


def xywh_to_xyxy(boxes_xywh):
    if isinstance(boxes_xywh, torch.Tensor):
        boxes_xyxy = boxes_xywh.clone()
    elif isinstance(boxes_xywh, np.ndarray):
        boxes_xyxy = boxes_xywh.copy()
    else:
        assert False, 'error: input must be a torch.Tensor or np.ndarray'

    boxes_xyxy[:, 0] = boxes_xywh[:, 0] - boxes_xywh[:, 2] / 2.0  # xmin = x_center - width / 2
    boxes_xyxy[:, 1] = boxes_xywh[:, 1] - boxes_xywh[:, 3] / 2.0  # ymin = y_center - height / 2
    boxes_xyxy[:, 2] = boxes_xywh[:, 0] + boxes_xywh[:, 2] / 2.0  # xmax = x_center + width / 2
    boxes_xyxy[:, 3] = boxes_xywh[:, 1] + boxes_xywh[:, 3] / 2.0  # ymax = y_center + height / 2

    return boxes_xyxy


def update_bounding_boxes(bounding_boxes, old_points, new_points, status):
    """
    Updates bounding box positions based on the average movement of tracked points.

    Parameters:
    - bounding_boxes: List of current bounding boxes as (x, y, w, h).
    - old_points: Numpy array of points in the previous frame.
    - new_points: Numpy array of points in the current frame.
    - status: Numpy array indicating whether each point has been successfully tracked (1) or not (0).

    Returns:
    - Updated list of bounding boxes.
    """
    updated_boxes = []
    point_movements = new_points - old_points

    for box in bounding_boxes:
        # Extract points that are within this bounding box
        x, y, w, h = box
        points_in_box = ((old_points[:, 0, 0] >= x) & (old_points[:, 0, 0] < x + w) &
                         (old_points[:, 0, 1] >= y) & (old_points[:, 0, 1] < y + h)).reshape(-1)

        valid_points_in_box = points_in_box & (status.flatten() == 1)

        if not np.any(valid_points_in_box):
            updated_boxes.append(box)
            continue

        average_movement = np.mean(point_movements[valid_points_in_box], axis=0).reshape(-1)

        if average_movement.size != 2:
            # If average_movement does not have exactly 2 elements, skip updating this box
            print("Error calculating average movement. Expected size 2, got:", average_movement.size)
            updated_boxes.append(box)
            continue

        # Safely access the average movements
        dx, dy = average_movement[0], average_movement[1]
        updated_box = (x + int(dx), y + int(dy), w, h)
        updated_boxes.append(updated_box)

    return updated_boxes


def select_key_points(bounding_boxes, gray_image, max_corners=40, quality_level=0.01, min_distance=20):
    """
    Selects key points within car bounding boxes using the Shi-Tomasi corner detection algorithm.

    Parameters:
    - bounding_boxes: A list of bounding boxes, where each box is represented as (x, y, w, h).
    - gray_image: The grayscale version of the current frame.
    - max_corners: The maximum number of corners to return. If there are more corners than are found,
      the strongest of them will be returned.
    - quality_level: Parameter characterizing the minimal accepted quality of image corners;
      the value of the parameter is multiplied by the best corner quality measure, which is the minimum eigenvalue
      (see cornerMinEigenVal) or the Harris function response (see cornerHarris). The corners with the quality measure
      less than the product are rejected. For example, if the best corner has the quality measure = 1500,
      and the quality_level=0.01, then all the corners with the quality measure less than 15 are rejected.
    - min_distance: Minimum possible Euclidean distance between the returned corners.

    Returns:
    - An array of points to track, in the format needed for cv2.calcOpticalFlowPyrLK.
    """
    points = []
    for (x, y, w, h) in bounding_boxes:
        # Defining the ROI for the current bounding box
        roi = gray_image[y:y + h, x:x + w]
        # Detecting corners in the ROI
        corners = cv2.goodFeaturesToTrack(roi, maxCorners=max_corners, qualityLevel=quality_level,
                                          minDistance=min_distance)
        if corners is not None:
            # Adjusting corner positions to the full image coordinates
            corners = corners + np.array([x, y], dtype=np.float32)
            # for corner in corners:
            points.extend(corners.tolist())

    # Converting the list of points to a numpy array with the shape (n, 1, 2)
    if points:
        points = np.array(points, dtype=np.float32)
    else:
        # If no points were found, return an empty array with the correct shape
        points = np.empty((0, 1, 2), dtype=np.float32)

    return points


def tracking(prev_detection_frame, bbox, tracking_frame_list):
    if not tracking_frame_list:
        return []
    bbox = xyxy_to_xywh(np.asarray(bbox))

    grey_prev_frame = cv2.cvtColor(prev_detection_frame, cv2.COLOR_BGR2GRAY)

    key_points = select_key_points(bbox, grey_prev_frame, max_corners=max(len(bbox) * 5, 50))

    result = []
    for present_frame in tracking_frame_list:
        grey_present_frame = cv2.cvtColor(present_frame, cv2.COLOR_BGR2GRAY)
        new_points, status, error = cv2.calcOpticalFlowPyrLK(grey_prev_frame, grey_present_frame, key_points, None)


        if len(key_points) > 0 and len(new_points) > 0:
            bbox = update_bounding_boxes(bbox, key_points, new_points, status)
            result.append(xywh_to_xyxy(np.asarray(bbox)))
        else:
            print('no bbox')

        grey_prev_frame = grey_present_frame.copy()
        key_points = new_points[status == 1].reshape(-1, 1, 2)

    return result


class CarTracking:
    def __init__(self):
        pass

    def __call__(self, images: List[np.ndarray]):
        pass
