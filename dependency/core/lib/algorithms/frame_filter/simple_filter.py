import abc
from core.lib.common import ClassFactory, ClassType
from core.lib.common import LOGGER
from .base_filter import BaseFilter

__all__ = ('SimpleFilter',)


@ClassFactory.register(ClassType.GEN_FILTER, alias='simple')
class SimpleFilter(BaseFilter, abc.ABC):
    def __init__(self):
        self.frame_count = 0

    def __call__(self, system, frame) -> bool:
        fps_raw = int(system.raw_meta_data['fps'])
        fps = int(system.meta_data['fps'])
        fps = min(fps, fps_raw)
        fps_mode, skip_frame_interval, remain_frame_interval = self.get_fps_adjust_mode(fps_raw, fps)

        LOGGER.debug(f'[FPS] fps: {fps}')

        self.frame_count += 1
        if fps_mode == 'skip' and self.frame_count % skip_frame_interval == 0:
            LOGGER.debug('[filter return] False')
            return False

        if fps_mode == 'remain' and self.frame_count % remain_frame_interval != 0:
            LOGGER.debug('[filter return] False')

            return False

        LOGGER.debug('[filter return] True')

        return True

    @staticmethod
    def get_fps_adjust_mode(fps_raw, fps):
        skip_frame_interval = 0
        remain_frame_interval = 0
        if fps >= fps_raw:
            fps_mode = 'same'
        elif fps < fps_raw // 2:
            fps_mode = 'remain'
            remain_frame_interval = fps_raw // fps
        else:
            fps_mode = 'skip'
            skip_frame_interval = fps_raw // (fps_raw - fps)

        return fps_mode, skip_frame_interval, remain_frame_interval
