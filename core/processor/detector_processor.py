import numpy as np
from typing import List

from .processor import Processor


class DetectorProcessor(Processor):
    def __init__(self):
        super().__init__()

    def __call__(self, images: List[np.ndarray]):
        raise NotImplementedError
