import abc

from core.lib.common import ClassFactory, ClassType
from core.lib.common import VideoOps
from core.lib.common import LOGGER
from .base_process import BaseProcess

__all__ = ('SimpleProcess',)


@ClassFactory.register(ClassType.GEN_PROCESS, alias='simple')
class SimpleProcess(BaseProcess, abc.ABC):
    def __init__(self):
        pass

    def __call__(self, system, frame):
        import cv2

        resolution = VideoOps.text2resolution(system.meta_data['resolution'])
        LOGGER.debug(f'[Frame Process] raw: {frame.shape} / new:{resolution}')
        return cv2.resize(frame, resolution)
