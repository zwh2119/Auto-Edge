import abc
from core.lib.common import ClassFactory, ClassType

from .base_agent import BaseAgent

__all__ = ('HEIAgent',)


@ClassFactory.register(ClassType.SCH_AGENT, alias='hei')
class HEIAgent(BaseAgent, abc.ABC):

    def __init__(self):
        pass

    def get_schedule_plan(self, info):
        pass

    def run(self, scheduler):
        pass

    def update_scenario(self, scenario):
        pass

    def update_resource(self, resource):
        pass