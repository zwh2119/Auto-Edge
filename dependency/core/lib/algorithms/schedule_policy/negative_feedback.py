import abc
from lib.common import ClassFactory, ClassType

from .base_policy import BasePolicy

__all__ = ('NegativeFeedback',)


@ClassFactory.register(ClassType.SCHEDULE_POLICY, alias='negative_feedback')
class NegativeFeedback(BasePolicy, abc.ABC):
    def __init__(self):
        pass

    def __call__(self):
        pass
