import abc
from lib.common import ClassFactory, ClassType

from .base_policy import BasePolicy

__all__ = ('HieraticalEmbodiedIntelligence',)


@ClassFactory.register(ClassType.SCHEDULE_POLICY, alias='hieratical_embodied_intelligence')
class HieraticalEmbodiedIntelligence(BasePolicy, abc.ABC):
    def __init__(self):
        pass

    def __call__(self):
        pass
