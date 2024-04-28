import abc

import cv2

from core.lib.common import ClassFactory, ClassType
from core.lib.common import VideoOps
from .base_process import BaseProcess

__all__ = ('SimpleProcess',)


@ClassFactory.register(ClassType.GEN_PROCESS, alias='simple')
class SimpleProcess(BaseProcess, abc.ABC):
    def __init__(self):
        pass

    def __call__(self, system, frame):
        resolution = VideoOps.text2resolution(system.meta_data['resolution'])
        return cv2.resize(frame, resolution)
