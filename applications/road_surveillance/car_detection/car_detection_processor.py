import numpy as np
from typing import List

from core.processor.detector_processor import DetectorProcessor
from core.lib.common import ClassFactory, ClassType

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

        detection_output = self.detector(detection_list)
        result_bbox, result_prob, result_class = detection_output[0]

        tracking_output = self.tracker(detection_list[0], result_bbox, tracking_list)

        process_output = [(bbox, result_prob, result_class, points) for bbox,points in zip(tracking_output[0], tracking_output[1])]
        process_output.insert(0, (result_bbox, result_prob, result_class, tracking_output[2]))

        return process_output
