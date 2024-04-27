
import numpy as np
from typing import List

from core.processor import DetectorProcessor
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




