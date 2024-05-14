import abc
from core.lib.common import ClassFactory, ClassType

from .base_agent import BaseAgent

__all__ = ('FixedAgent',)


@ClassFactory.register(ClassType.SCH_AGENT, alias='fixed')
class FixedAgent(BaseAgent, abc.ABC):

    def __init__(self, system, fixed_policy: dict = None):
        self.cloud_device = system.cloud_device
        self.fixed_policy = fixed_policy

    def get_schedule_plan(self, info):
        if self.fixed_policy is None:
            return self.fixed_policy

        policy = self.fixed_policy.copy()
        edge_device = info['device']
        cloud_device = self.cloud_device
        pipe_seg = policy['pipeline']
        pipeline = info['pipeline']
        pipeline = [p.update('execute_device', edge_device) for p in pipeline[:pipe_seg]] + \
                   [p.update('execute_device', cloud_device) for p in pipeline[pipe_seg:]]

        policy.update({'pipeline': pipeline})
        return policy

    def run(self, scheduler):
        pass

    def update_scenario(self, scenario):
        pass

    def update_resource(self, resource):
        pass
