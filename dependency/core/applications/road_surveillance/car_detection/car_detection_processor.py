
import numpy as np
from typing import List

from core.processor import DetectorProcessor
from core.lib.common import ClassFactory, ClassType
from core.lib.estimation import Timer

from .car_detection import CarDetection
from .car_tracking import CarTracking

__all__ = ('CarDetectionProcessor',)


@ClassFactory.register(ClassType.PRO_DETECTOR, alias='car_detection')
class CarDetectionProcessor(DetectorProcessor):
    def __init__(self, weights, plugin, device=0):
        super().__init__()

        self.detector = CarDetection(weights, plugin, device)
        self.tracker = CarTracking()

    def __call__(self, images: List[np.ndarray]):
        assert images, 'Input images is empty'

        detection_list = images[0:1]
        tracking_list = images[1:]
        with Timer(f'Detection / {len(detection_list)} frame'):
            detection_output = self.detector(detection_list)
        result_bbox, result_prob, result_class = detection_output[0]
        with Timer(f'Tracking / {len(tracking_list)} frame'):
            tracking_output = self.tracker(tracking_list, detection_list[0], (result_bbox, result_prob, result_class))
        process_output = tracking_output

        return process_output
