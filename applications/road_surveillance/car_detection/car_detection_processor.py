import numpy as np
from typing import List

from core.processor.detector_processor import DetectorProcessor
from core.lib.common import ClassFactory, ClassType


@ClassFactory.register(ClassType.PRO_DETECTOR, alias='car_detection')
class CarDetectionProcessor(DetectorProcessor):
    def __init__(self):
        super().__init__()

    def __call__(self, images: List[np.ndarray]):
        pass
