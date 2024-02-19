import abc
from lib.common import ClassFactory, ClassType

__all__ = ('SimpleCompress',)


class BaseCompress(metaclass=abc.ABCMeta):
    def __call__(self):
        raise NotImplementedError


@ClassFactory.register(ClassType.GEN_COMPRESS, alias='simple')
class SimpleCompress(BaseCompress, abc.ABC):
    def __init__(self):
        pass

    def __call__(self):
        pass
