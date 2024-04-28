import abc


class BaseProcess(metaclass=abc.ABCMeta):
    def __call__(self, system, frame):
        raise NotImplementedError
