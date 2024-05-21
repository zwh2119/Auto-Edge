import abc
import threading
import time

import numpy as np

from core.lib.common import ClassFactory, ClassType, LOGGER, FileOps

from .base_agent import BaseAgent

__all__ = ('HEIAgent',)


@ClassFactory.register(ClassType.SCH_AGENT, alias='hei')
class HEIAgent(BaseAgent, abc.ABC):

    def __init__(self, system,
                 hyper_params: dict = None,
                 drl_params: dict = None,
                 window_size: int = 10,
                 mode: str = 'inference'):
        from hei import SoftActorCritic, RandomBuffer, Adapter, NegativeFeedback, StateBuffer

        self.window_size = window_size
        self.state_buffer = StateBuffer(self.window_size)
        self.mode = mode

        self.drl_agent = SoftActorCritic(**drl_params)
        self.replay_buffer = RandomBuffer(**drl_params)
        self.adapter = Adapter

        self.nf_agent = NegativeFeedback()

        self.drl_schedule_interval = hyper_params['drl_schedule_interval']
        self.nf_schedule_interval = hyper_params['nf_schedule_interval']

        self.state_dim = drl_params['state_dim']
        self.action_dim = drl_params['action_dim']

        self.model_dir = hyper_params['model_dir']
        FileOps.create_directory(self.model_dir)

        if hyper_params['load_model']:
            self.drl_agent.load(self.model_dir, hyper_params['load_model_episode'])

        self.total_steps = hyper_params['drl_total_steps']
        self.save_interval = hyper_params['drl_save_interval']
        self.update_interval = hyper_params['drl_update_interval']
        self.update_after = hyper_params['drl_update_after']

        self.intermediate_decision = [0 for _ in range(self.action_dim)]

        self.schedule_plan = None

    def get_drl_state_buffer(self):

        # TODO: normalization the state ?
        resources = self.state_buffer.get_resource_buffer()
        scenarios = self.state_buffer.get_scenario_buffer()

        while len(resources) == 0 or len(scenarios) == 0:
            time.sleep(2)
            LOGGER.info('[Wait for State] State empty, wait for resource state or scenario state ..')

        state = np.array((scenarios[:, 0], scenarios[:, 1], scenarios[:, 2], resources[:, 0]))

        return state

    def map_drl_action_to_decision(self, action):
        """
        map [-1, 1] to {-1, 0, 1}
        """

        # TODO: consider change to stochastic find result with distribution

        self.intermediate_decision = [int(np.sign(a)) if abs(a) > 0.3 else 0 for a in action]

    def reset_drl_env(self):
        self.intermediate_decision = [0 for _ in range(self.action_dim)]

        return self.get_drl_state_buffer()

    def step_drl_env(self, action):

        self.map_drl_action_to_decision(action)

        time.sleep(self.drl_schedule_interval)

        state = self.get_drl_state_buffer()
        reward = self.calculate_drl_reward()
        done = False
        info = ''

        return state, reward, done, info

    def calculate_drl_reward(self):

        # TODO

        return 0

    def train_drl_agent(self):
        LOGGER.info('[DRL Train] Start train drl agent ..')
        state = self.reset_drl_env()
        for step in range(self.total_steps):
            action = self.drl_agent.select_action(state, deterministic=False, with_logprob=False)

            next_state, reward, done, info = self.step_drl_env(action)
            done = self.adapter.done_adapter(done, step)
            self.replay_buffer.add(state, action, reward, next_state, done)
            state = next_state

            if step >= self.update_after and step % self.update_interval == 0:
                for _ in range(self.update_interval):
                    self.drl_agent.train(self.replay_buffer)

            if step % self.save_interval:
                self.drl_agent.save(self.model_dir, step)

            if done:
                state = self.reset_drl_env()

        LOGGER.info('[DRL Train] End train drl agent ..')

    def inference_drl_agent(self):
        LOGGER.info('[DRL Inference] Start inference drl agent ..')

        while True:
            time.sleep(self.drl_schedule_interval)

    def run_nf_agent(self):
        LOGGER.info('[NF Inference] Start inference nf agent ..')

        while True:
            time.sleep(self.nf_schedule_interval)

    def update_scenario(self, scenario):
        object_number = np.mean(scenario['obj_num'])
        object_size = np.mean(scenario['obj_size'])
        task_delay = scenario['delay']
        self.state_buffer.add_scenario_buffer([object_number, object_size, task_delay])

    def update_resource(self, resource):
        bandwidth = resource['bandwidth']
        if bandwidth != 0:
            self.state_buffer.add_resource_buffer([bandwidth])

    def get_schedule_plan(self, info):
        return self.schedule_plan

    def run(self):
        threading.Thread(target=self.run_nf_agent).start()

        if self.mode == 'train':
            self.train_drl_agent()
        elif self.mode == 'inference':
            self.inference_drl_agent()
        else:
            assert None, f'Invalid execution mode: {self.mode}, only support ["train", "inference"]'
