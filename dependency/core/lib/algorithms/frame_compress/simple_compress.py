import abc

from core.lib.common import ClassFactory, ClassType
from .base_compress import BaseCompress

__all__ = ('SimpleCompress',)


@ClassFactory.register(ClassType.GEN_COMPRESS, alias='simple')
class SimpleCompress(BaseCompress, abc.ABC):
    def __init__(self):
        pass

    def __call__(self, system, frame_buffer, source_id, task_id):
        import cv2

        assert frame_buffer, 'frame buffer is empty!'
        fourcc = cv2.VideoWriter_fourcc(*system.meta_data['encoding'])
        height, width, _ = frame_buffer[0].shape
        buffer_path = self.generate_file_path(source_id, task_id)
        out = cv2.VideoWriter(buffer_path, fourcc, 30, (width, height))
        for frame in frame_buffer:
            out.write(frame)
        out.release()

        return buffer_path

    @staticmethod
    def generate_file_path(source_id, task_id):
        return f'video_source_{source_id}_task_{task_id}.mp4'
