import abc
from core.lib.common import ClassFactory, ClassType

from .base_agent import BaseAgent

__all__ = ('NegativeFeedback',)


@ClassFactory.register(ClassType.SCH_AGENT, alias='negative_feedback')
class NegativeFeedback(BaseAgent, abc.ABC):
    def __init__(self):
        pass

    def __call__(self):
        pass
