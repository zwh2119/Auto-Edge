import abc
from core.lib.common import ClassFactory, ClassType

from .base_agent import BaseAgent

__all__ = ('HieraticalEmbodiedIntelligence',)


@ClassFactory.register(ClassType.SCH_AGENT, alias='hieratical_embodied_intelligence')
class HieraticalEmbodiedIntelligence(BaseAgent, abc.ABC):
    def __init__(self):
        pass

    def __call__(self):
        pass
