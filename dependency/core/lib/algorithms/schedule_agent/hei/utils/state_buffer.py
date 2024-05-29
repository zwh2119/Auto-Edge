import numpy as np
from core.lib.common import LOGGER


class StateBuffer:
    def __init__(self, window_size, max_size=10000):
        self.resources = []
        self.scenarios = []
        self.decisions = []

        self.window_size = window_size
        self.max_size = max_size

    def add_resource_buffer(self, resource):
        self.resources.append(resource)
        while len(self.resources) > self.max_size:
            self.resources.pop(0)

    def add_scenario_buffer(self, scenario):
        self.scenarios.append(scenario)
        while len(self.scenarios) > self.max_size:
            self.scenarios.pop(0)

    def add_decision_buffer(self, decision):
        self.decisions.append(decision)
        while len(self.decisions) > self.max_size:
            self.decisions.pop(0)

    def get_resource_buffer(self):
        return np.array(self.resources.copy())

    def get_scenario_buffer(self):
        return np.array(self.scenarios.copy())

    def get_decision_buffer(self):
        return np.array(self.decisions.copy())

    def get_state_buffer(self):

        # TODO: normalization the state ?
        resources = self.resources.copy()
        scenarios = self.scenarios.copy()
        decisions = self.decisions.copy()

        if len(resources) == 0 or len(scenarios) == 0 or len(decisions) == 0:
            self.clear_state_buffer()
            return None

        LOGGER.debug(f'[Resource Buffer] length: {len(resources)}, content: {resources}')
        LOGGER.debug(f'[Scenario Buffer] length: {len(scenarios)}, content: {scenarios}')

        resources = np.array(self.resample_buffer(resources, self.window_size))
        scenarios = np.array(self.resample_buffer(scenarios, self.window_size))
        decisions = np.array(self.resample_buffer(decisions, self.window_size))

        LOGGER.debug(f'[Resample Resource Buffer] length: {len(resources)}, content: {resources}')
        LOGGER.debug(f'[Resample Scenario Buffer] length: {len(scenarios)}, content: {scenarios}')

        state = np.vstack((resources.T, scenarios.T, decisions.T))
        self.clear_state_buffer()
        return state

    def clear_state_buffer(self):
        self.resources.clear()
        self.scenarios.clear()
        self.decisions.copy()

    @staticmethod
    def resample_buffer(buffer, size):
        buffer_length = len(buffer)
        assert buffer_length != 0, 'Resample buffer size is 0!'

        if buffer_length > size:
            indices = np.linspace(0, buffer_length - 1, num=size, dtype=int)
            resized_buffer = [buffer[idx] for idx in indices]
        elif buffer_length < size:
            resized_buffer = []
            repeat_factor = size // buffer_length
            extra_slots = size % buffer_length
            for i in range(buffer_length):
                resized_buffer.extend([buffer[i]] * repeat_factor)
                if extra_slots > 0:
                    resized_buffer.append(buffer[i])
                    extra_slots -= 1
        else:
            resized_buffer = buffer[:]
        return resized_buffer
