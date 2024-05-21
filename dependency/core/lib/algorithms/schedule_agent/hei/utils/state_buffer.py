import numpy as np


class StateBuffer:
    def __init__(self, window_size, max_size=10000):
        self.resources = []
        self.scenarios = []

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

    def get_resource_buffer(self):
        return np.array(self.resources.copy())

    def get_scenario_buffer(self):
        return np.array(self.scenarios.copy())

    def get_state_buffer(self):

        # TODO: normalization the state ?
        resources = self.resources.copy()
        scenarios = self.scenarios.copy()
        if len(resources) == 0 or len(scenarios) == 0:
            return None

    def clear_state_buffer(self):
        self.resources.clear()
        self.scenarios.clear()
