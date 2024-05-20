import abc
import numpy as np

from core.lib.common import ClassFactory, ClassType, LOGGER

from .base_agent import BaseAgent

__all__ = ('HEIAgent',)


@ClassFactory.register(ClassType.SCH_AGENT, alias='hei')
class HEIAgent(BaseAgent, abc.ABC):

    def __init__(self, system,
                 drl_params: dict = None,
                 window_size: int = 10,
                 mode: str = 'inference'):
        from hei import SoftActorCritic, RandomBuffer

        self.resources = []
        self.scenarios = []

        self.window_size = window_size
        self.mode = mode

        self.drl_agent = SoftActorCritic(**drl_params)
        self.replay_buffer = RandomBuffer(**drl_params)

        self.nf_agent = None

        self.state_dim = drl_params['state_dim']
        self.action_dim = drl_params['action_dim']

        self.schedule_plan = None

    def get_schedule_plan(self, info):
        return self.schedule_plan

    def run(self):
        if self.mode == 'train':
            self.train_drl_agent()
        elif self.mode == 'inference':
            pass
        else:
            assert None, f'Invalid execution mode: {self.mode}, only support ["train", "inference"]'

    def train_drl_agent(self):
        LOGGER.info('[DRL Train] Start train drl agent..')
        while True:
            pass

    def calculate_reward(self):
        pass

    def get_state_buffer(self):
        resources = self.resources.copy()
        scenarios = self.scenarios.copy()

        state = []

        LOGGER.debug('[State Buffer]')

    def add_resource_buffer(self, resource):
        self.resources.append(resource)
        while len(self.resources) > self.window_size:
            self.resources.pop(0)

    def add_scenario_buffer(self, scenario):
        self.scenarios.append(scenario)
        while len(self.scenarios) > self.window_size:
            self.scenarios.pop(0)

    def update_scenario(self, scenario):
        object_number = np.mean(scenario['obj_num'])
        object_size = np.mean(scenario['obj_size'])
        task_delay = scenario['delay']
        self.add_scenario_buffer([object_number,object_size, task_delay])

    def update_resource(self, resource):
        bandwidth = resource['bandwidth']
        if bandwidth != 0:
            self.add_resource_buffer([bandwidth])
