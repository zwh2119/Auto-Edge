from core.lib.common import LOGGER


class NegativeFeedback:
    def __init__(self, system):
        self.fps_list = system.fps_list
        self.resolution_list = system.resolution_list
        self.buffer_size_list = system.buffer_size_list
        self.pipeline_list = None

        self.schedule_knobs = system.schedule_knobs

    def __call__(self, latest_policy, meta_decision):
        if latest_policy is None:
            LOGGER.info('[Lack Latest Policy] No latest policy, none decision make ..')
            return None

        resolution = latest_policy['resolution']
        fps = latest_policy['fps']
        buffer_size = latest_policy['buffer_size']
        pipeline = latest_policy['pipeline']

    @staticmethod
    def map_knob_to_index(knob, knob_value_list: list):
        return knob_value_list.index(knob)

    @staticmethod
    def map_index_to_knob(index, knob_value_list: list):
        pass

    def increase_knob(self):
        pass

    def decrease_knob(self):
        pass
