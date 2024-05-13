import abc
from core.lib.common import ClassFactory, ClassType

from .base_agent import BaseAgent

__all__ = ('HieraticalEmbodiedIntelligence',)


@ClassFactory.register(ClassType.SCH_AGENT, alias='hieratical_embodied_intelligence')
class HieraticalEmbodiedIntelligence(BaseAgent, abc.ABC):

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