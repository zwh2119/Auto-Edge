import abc
import os.path
import threading
import time

from core.lib.common import ClassFactory, ClassType, LOGGER, FileOps, Context

from .base_agent import BaseAgent

__all__ = ('HEIAgent',)


@ClassFactory.register(ClassType.SCH_AGENT, alias='hei')
class HEIAgent(BaseAgent, abc.ABC):

    def __init__(self, system,
                 agent_id: int,
                 window_size: int = 10,
                 mode: str = 'inference'):
        from .hei import SoftActorCritic, RandomBuffer, Adapter, NegativeFeedback, StateBuffer

        self.agent_id = agent_id

        drl_params = system.drl_params.copy()
        hyper_params = system.hyper_params.copy()
        drl_params['state_dim'] = [drl_params['state_dim'], window_size]

        self.window_size = window_size
        self.state_buffer = StateBuffer(self.window_size)
        self.mode = mode

        self.drl_agent = SoftActorCritic(**drl_params)
        self.replay_buffer = RandomBuffer(**drl_params)
        self.adapter = Adapter

        self.nf_agent = NegativeFeedback(system, agent_id)

        self.drl_schedule_interval = hyper_params['drl_schedule_interval']
        self.nf_schedule_interval = hyper_params['nf_schedule_interval']

        self.state_dim = drl_params['state_dim']
        self.action_dim = drl_params['action_dim']

        self.model_dir = Context.get_file_path(os.path.join(hyper_params['model_dir'], f'agent_{self.agent_id}'))
        FileOps.create_directory(self.model_dir)

        if hyper_params['load_model']:
            self.drl_agent.load(self.model_dir, hyper_params['load_model_episode'])

        self.total_steps = hyper_params['drl_total_steps']
        self.save_interval = hyper_params['drl_save_interval']
        self.update_interval = hyper_params['drl_update_interval']
        self.update_after = hyper_params['drl_update_after']

        self.intermediate_decision = [0 for _ in range(self.action_dim)]

        self.latest_policy = None
        self.schedule_plan = None

    def get_drl_state_buffer(self):
        while True:
            state = self.state_buffer.get_state_buffer()
            if state is not None:
                return state
            LOGGER.info(f'[Wait for State] (agent {self.agent_id}) State empty, '
                        f'wait for resource state or scenario state ..')
            time.sleep(1)

    def map_drl_action_to_decision(self, action):
        """
        map [-1, 1] to {-1, 0, 1}
        """
        import numpy as np

        self.intermediate_decision = [int(np.sign(a)) if abs(a) > 0.3 else 0 for a in action]

        LOGGER.info(f'[DRL Decision] (agent {self.agent_id}) Action: {action}   Decision:{self.intermediate_decision}')

    def reset_drl_env(self):
        self.intermediate_decision = [0 for _ in range(self.action_dim)]

        return self.get_drl_state_buffer()

    def step_drl_env(self, action):

        self.map_drl_action_to_decision(action)

        time.sleep(self.drl_schedule_interval)

        state = self.get_drl_state_buffer()
        reward = self.calculate_drl_reward(state)
        done = False
        info = ''

        return state, reward, done, info

    @staticmethod
    def calculate_drl_reward(state):

        # delay as reward calculation
        return - state[2].mean()

    def train_drl_agent(self):
        LOGGER.info(f'[DRL Train] (agent {self.agent_id}) Start train drl agent ..')
        state = self.reset_drl_env()
        for step in range(self.total_steps):
            action = self.drl_agent.select_action(state, deterministic=False, with_logprob=False)

            next_state, reward, done, info = self.step_drl_env(action)
            done = self.adapter.done_adapter(done, step)
            self.replay_buffer.add(state, action, reward, next_state, done)
            state = next_state

            LOGGER.info(f'[DRL Train Data] (agent {self.agent_id}) Step:{step}  Reward:{reward}')

            if step >= self.update_after and step % self.update_interval == 0:
                for _ in range(self.update_interval):
                    LOGGER.info(f'[DRL Train] (agent {self.agent_id}) Train drl agent with replay buffer')
                    self.drl_agent.train(self.replay_buffer)

            if step % self.save_interval:
                self.drl_agent.save(self.model_dir, step)

            if done:
                state = self.reset_drl_env()

        LOGGER.info(f'[DRL Train] (agent {self.agent_id}) End train drl agent ..')

    def inference_drl_agent(self):
        LOGGER.info(f'[DRL Inference] (agent {self.agent_id}) Start inference drl agent ..')
        state = self.reset_drl_env()
        cur_step = 0
        while True:
            time.sleep(self.drl_schedule_interval)
            cur_step += 1
            action = self.drl_agent.select_action(state, deterministic=False, with_logprob=False)
            next_state, reward, done, info = self.step_drl_env(action)
            done = self.adapter.done_adapter(done, cur_step)
            state = next_state
            if done:
                state = self.reset_drl_env()
                cur_step = 0

    def run_nf_agent(self):
        LOGGER.info(f'[NF Inference] (agent {self.agent_id}) Start inference nf agent ..')

        while True:
            time.sleep(self.nf_schedule_interval)

            self.schedule_plan = self.nf_agent(self.latest_policy, self.intermediate_decision)
            LOGGER.debug(f'[NF Update] (agent {self.agent_id}) schedule: {self.schedule_plan}')

    def update_scenario(self, scenario):
        import numpy as np
        object_number = np.mean(scenario['obj_num'])
        object_size = np.mean(scenario['obj_size'])
        task_delay = scenario['delay']

        # TODO
        resolution_decision = None
        fps_decision = None
        buffer_size_decision = None
        pipeline_decision = None

        self.state_buffer.add_scenario_buffer([object_number, object_size, task_delay])
        self.state_buffer.add_decision_buffer([resolution_decision, fps_decision,
                                               buffer_size_decision, pipeline_decision])

    def update_resource(self, resource):
        bandwidth = resource['bandwidth']
        if bandwidth != 0:
            self.state_buffer.add_resource_buffer([bandwidth])

    def update_latest_policy(self, policy):
        self.latest_policy = policy

    def get_schedule_plan(self, info):
        return self.schedule_plan

    def run(self):
        threading.Thread(target=self.run_nf_agent).start()

        if self.mode == 'train':
            self.train_drl_agent()
        elif self.mode == 'inference':
            self.inference_drl_agent()
        else:
            assert None, f'(agent {self.agent_id}) Invalid execution mode: {self.mode}, ' \
                         f'only support ["train", "inference"]'
