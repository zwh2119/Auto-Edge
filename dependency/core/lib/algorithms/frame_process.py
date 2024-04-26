import abc

import cv2

from lib.common import ClassFactory, ClassType
from lib.common import VideoOps

__all__ = ('SimpleProcess',)


class BaseProcess(metaclass=abc.ABCMeta):
    def __call__(self, system, frame):
        raise NotImplementedError


@ClassFactory.register(ClassType.GEN_PROCESS, alias='simple')
class SimpleProcess(BaseProcess, abc.ABC):
    def __init__(self):
        pass

    def __call__(self, system, frame):
        resolution = VideoOps.text2resolution(system.meta_data['resolution'])
        return cv2.resize(frame, resolution)

