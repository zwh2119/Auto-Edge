import abc
from lib.common import ClassFactory, ClassType

__all__ = ('SimpleFilter',)


class BaseFilter(metaclass=abc.ABCMeta):
    def __call__(self, frame_buffer, frame) -> bool:
        raise NotImplementedError


@ClassFactory.register(ClassType.GEN_FILTER, alias='simple')
class SimpleFilter(BaseFilter, abc.ABC):
    def __init__(self):
        pass

    def __call__(self, frame_buffer, frame) -> bool:
        return True
