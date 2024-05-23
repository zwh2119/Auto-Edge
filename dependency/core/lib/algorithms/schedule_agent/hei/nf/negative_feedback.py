from core.lib.common import LOGGER


class NegativeFeedback:
    def __init__(self, system, agent_id):
        self.agent_id = agent_id

        self.fps_list = system.fps_list.copy()
        self.resolution_list = system.resolution_list.copy()
        self.buffer_size_list = system.buffer_size_list.copy()
        self.pipeline_list = None

        self.cloud_device = system.cloud_device
        self.edge_device = None

        self.schedule_knobs = system.schedule_knobs.copy()

    def __call__(self, latest_policy: dict, meta_decisions: list):

        assert len(meta_decisions) == len(self.schedule_knobs), \
            f'decision length {len(meta_decisions)} is not equal to number schedule knobs {len(self.schedule_knobs)} !'

        if latest_policy is None:
            LOGGER.info(f'[NF Lack Latest Policy] (agent {self.agent_id}) No latest policy, none decision make ..')
            return None

        resolution = latest_policy['resolution']
        fps = latest_policy['fps']
        buffer_size = latest_policy['buffer_size']
        pipeline = latest_policy['pipeline']

        self.pipeline_list = list(range(0, len(pipeline)))
        self.edge_device = latest_policy['edge_device']

        self.resolution_index = self.resolution_list.index(resolution)
        self.fps_index = self.fps_list.index(fps)
        self.buffer_size_index = self.buffer_size_list.index(buffer_size)
        self.pipeline_index = next((i for i, service in enumerate(pipeline)
                                    if service['execute_device'] == self.cloud_device), len(pipeline) - 1)

        # TODO: should increase / decrease equally?
        for idx, knob_name in enumerate(self.schedule_knobs):
            knob_decision = meta_decisions[idx]
            knob_index = getattr(self, f'{knob_name}_index')
            knob_list = getattr(self, f'{knob_name}_list')
            if knob_decision == 1:
                updated_knob_index = self.increase_knob(knob_index, knob_list)
                LOGGER.info(f'[NF Schedule] (agent {self.agent_id}) Knob {knob_name} increase: index {knob_index}->{updated_knob_index}')
            elif knob_decision == -1:
                updated_knob_index = self.decrease_knob(knob_index, knob_list)
                LOGGER.info(f'[NF Schedule] (agent {self.agent_id}) Knob {knob_name} decrease: index {knob_index}->{updated_knob_index}')
            elif knob_decision == 0:
                updated_knob_index = knob_index
                LOGGER.info(f'[NF Schedule] (agent {self.agent_id}) Knob {knob_name} remain same: index {knob_index}')
            else:
                updated_knob_index = 0
                assert None, f'(agent {self.agent_id}) Invalid Knob schedule decision {knob_decision} of Knob {knob_name}'

            setattr(self, f'{knob_name}_index', updated_knob_index)

        schedule_policy = {}
        schedule_policy.update(latest_policy)
        schedule_policy['resolution'] = self.resolution_list[self.resolution_index]
        schedule_policy['fps'] = self.fps_list[self.fps_index]
        schedule_policy['buffer_size'] = self.buffer_size_list[self.buffer_size_index]
        schedule_policy['pipeline'] = [{**p, 'execute_device': self.edge_device} for p in
                                       pipeline[:self.pipeline_index]] + \
                                      [{**p, 'execute_device': self.cloud_device} for p in
                                       pipeline[self.pipeline_index:]]

        return schedule_policy

    @staticmethod
    def increase_knob(knob_index, knob_list):
        assert 0 <= knob_index < len(knob_list), \
            f'Index of Knob is out of range (index:{knob_index}, range:[0,{len(knob_list) - 1}])'
        return min(knob_index + 1, len(knob_list) - 1)

    @staticmethod
    def decrease_knob(knob_index, knob_list):
        assert 0 <= knob_index < len(knob_list), \
            f'Index of Knob is out of range (index:{knob_index}, range:[0,{len(knob_list) - 1}])'
        return max(knob_index - 1, 0)
