import abc
from core.lib.common import ClassFactory, ClassType

from .base_agent import BaseAgent

__all__ = ('FixedAgent',)


@ClassFactory.register(ClassType.SCH_AGENT, alias='fixed')
class FixedAgent(BaseAgent, abc.ABC):

    def get_schedule_plan(self, info):
        return {
            'resolution': '720p',
            'fps': 30,
            'encoding': 'mp4v',
            'batch_size': 8,
            'pipeline': info['pipeline']
        }

    def run(self, scheduler):
        pass

    def update_scenario(self, scenario):
        pass

    def update_resource(self, resource):
        pass
