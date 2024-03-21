import abc
import cv2

from lib.common import ClassFactory, ClassType

__all__ = ('SimpleCompress',)


class BaseCompress(metaclass=abc.ABCMeta):
    def __call__(self, system, frame_buffer):
        raise NotImplementedError


@ClassFactory.register(ClassType.GEN_COMPRESS, alias='simple')
class SimpleCompress(BaseCompress, abc.ABC):
    def __init__(self):
        pass

    def __call__(self, system, frame_buffer):
        assert frame_buffer, 'frame buffer is empty!'
        fourcc = cv2.VideoWriter_fourcc(*system.meta_data['encoding'])
        height, width, _ = frame_buffer[0].shape
        buffer_path = f'temp_{system.source_id}.mp4'
        out = cv2.VideoWriter(buffer_path, fourcc, 30, (width, height))
        for frame in frame_buffer:
            out.write(frame)
        out.release()

        return buffer_path

