import abc
from core.lib.common import ClassFactory, ClassType

from .base_agent import BaseAgent

__all__ = ('FixedAgent',)


@ClassFactory.register(ClassType.SCH_AGENT, alias='fixed')
class FixedAgent(BaseAgent, abc.ABC):

    def __call__(self):
        pass

    def run(self, scheduler):
        pass
