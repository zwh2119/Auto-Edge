import abc
from lib.common import ClassFactory, ClassType

__all__ = ('SimpleProcess',)


class BaseProcess(metaclass=abc.ABCMeta):
    def __call__(self):
        raise NotImplementedError


@ClassFactory.register(ClassType.GEN_PROCESS, alias='simple')
class SimpleProcess(BaseProcess, abc.ABC):
    def __init__(self):
        pass

    def __call__(self):
        pass
