import abc


class BaseFilter(metaclass=abc.ABCMeta):
    def __call__(self, system, frame) -> bool:
        raise NotImplementedError
