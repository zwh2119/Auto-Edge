import numpy as np
from typing import List
import cv2

from .processor import Processor

from core.lib.estimation import Timer
from core.lib.content import Task
from core.lib.common import LOGGER, convert_ndarray_to_list


class DetectorProcessor(Processor):
    def __init__(self):
        super().__init__()

        self.detector = None
        self.tracker = None

        self.frame_size = None

    def __call__(self, task: Task):
        data_file_path = task.get_file_path()
        cap = cv2.VideoCapture(data_file_path)
        image_list = []
        success, frame = cap.read()
        while success:
            self.frame_size = (cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            image_list.append(frame)
            success, frame = cap.read()

        if len(image_list) == 0:
            LOGGER.critical('ERROR: image list length is 0')
            LOGGER.critical(f'Source: {task.get_source_id()}, Task: {task.get_task_id()}')
            LOGGER.critical(f'file_path: {task.get_file_path()}')
            return None
        result = self.infer(image_list)
        task = self.get_scenario(result, task)
        task.set_content(convert_ndarray_to_list(result))

        return task

    def infer(self, images: List[np.ndarray]):
        assert self.detector, 'No detector defined!'
        assert self.tracker, 'No tracker defined!'

        LOGGER.debug(f'[Batch Size] Car detection batch: {len(images)}')
        detection_list = images[0:1]
        tracking_list = images[1:]
        with Timer(f'Detection / {len(detection_list)} frame'):
            detection_output = self.detector(detection_list)
        result_bbox, result_prob, result_class = detection_output[0]
        with Timer(f'Tracking / {len(tracking_list)} frame'):
            tracking_output = self.tracker(tracking_list, detection_list[0], (result_bbox, result_prob, result_class))
        process_output = tracking_output

        return process_output

    def get_scenario(self, result, task):
        obj_num = []
        obj_size = []
        for frame_result in result:
            bboxes = frame_result[0]
            boxes_num = len(bboxes)
            boxes_size = 0 if boxes_num == 0 else \
                np.mean([((box[2] - box[0]) * (box[3] - box[1]))
                         / (self.frame_size[0] * self.frame_size[1]) for box in bboxes])
            obj_num.append(boxes_num)
            obj_size.append(boxes_size)

        task.add_scenario({'obj_num': obj_num, 'obj_size': obj_size})

        return task
