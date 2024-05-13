from typing import List

import numpy as np
from core.lib.content import Task


class Processor:
    def __init__(self):
        pass

    def __call__(self, task: Task):
        raise NotImplementedError
