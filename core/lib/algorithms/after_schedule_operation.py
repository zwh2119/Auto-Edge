import abc
from lib.common import ClassFactory, ClassType

__all__ = ('SimpleOperation',)


class BaseOperation(metaclass=abc.ABCMeta):
    def __call__(self, scheduler_policy):
        raise NotImplementedError


@ClassFactory.register(ClassType.GEN_ASO, alias='simple')
class SimpleOperation(BaseOperation, abc.ABC):
    def __init__(self):
        pass

    def __call__(self, scheduler_policy):
        pass
