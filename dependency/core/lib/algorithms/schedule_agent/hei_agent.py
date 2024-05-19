import abc
from core.lib.common import ClassFactory, ClassType

from .base_agent import BaseAgent

__all__ = ('HEIAgent',)


@ClassFactory.register(ClassType.SCH_AGENT, alias='hei')
class HEIAgent(BaseAgent, abc.ABC):

    def __init__(self, system,
                 drl_params: dict = None,
                 window_size: int = 10,
                 mode: str = 'inference'):
        from hei import SoftActorCritic

        self.resources = []
        self.scenarios = []

        self.window_size = window_size
        self.mode = mode

        self.drl_agent = SoftActorCritic(**drl_params)
        self.nf_agent = None

        self.schedule_plan = None

    def get_schedule_plan(self, info):
        return self.schedule_plan

    def run(self):
        if self.mode == 'train':
            pass
        elif self.mode == 'inference':
            pass
        else:
            assert None, f'Invalid execution mode: {self.mode}, only support ["train", "inference"]'

    def update_scenario(self, scenario):
        pass

    def update_resource(self, resource):
        pass
