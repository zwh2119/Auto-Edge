import abc
from lib.common import ClassFactory, ClassType

__all__ = ('NegativeFeedback', 'HieraticalEmbodiedIntelligence')


class BasePolicy(metaclass=abc.ABCMeta):
    def __call__(self):
        raise NotImplementedError


@ClassFactory.register(ClassType.SCHEDULE_POLICY, alias='negative_feedback')
class NegativeFeedback(BasePolicy, abc.ABC):
    def __init__(self):
        pass

    def __call__(self):
        pass


@ClassFactory.register(ClassType.SCHEDULE_POLICY, alias='hieratical_embodied_intelligence')
class HieraticalEmbodiedIntelligence(BasePolicy, abc.ABC):
    def __init__(self):
        pass

    def __call__(self):
        pass
