import abc


class BaseCompress(metaclass=abc.ABCMeta):
    def __call__(self, system, frame_buffer, source_id, task_id):
        raise NotImplementedError
