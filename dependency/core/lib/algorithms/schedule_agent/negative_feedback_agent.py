import abc
from core.lib.common import ClassFactory, ClassType

from .base_agent import BaseAgent

__all__ = ('NegativeFeedbackAgent',)


@ClassFactory.register(ClassType.SCH_AGENT, alias='nf')
class NegativeFeedbackAgent(BaseAgent, abc.ABC):
    def __init__(self):
        pass

    def __call__(self):
        pass
