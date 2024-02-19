import abc
from lib.common import ClassFactory, ClassType

__all__ = ('SimpleOperation',)


class BaseOperation(metaclass=abc.ABCMeta):
    def __call__(self, generator):
        raise NotImplementedError


@ClassFactory.register(ClassType.GEN_BSO, alias='simple')
class SimpleOperation(BaseOperation, abc.ABC):
    def __init__(self):
        pass

    def __call__(self, generator):
        pass
