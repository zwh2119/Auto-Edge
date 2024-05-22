from core.lib.common import LOGGER


class NegativeFeedback:
    def __init__(self, system):
        self.fps_list = system.fps_list
        self.resolution_list = system.resolution_list
        self.buffer_size_list = system.buffer_size_list

        self.schedule_knobs = system.schedule_knobs

    def __call__(self, latest_policy, meta_decision):
        if latest_policy is None:
            LOGGER.info('[Lack Latest Policy] No latest policy, none decision make ..')
            return None
