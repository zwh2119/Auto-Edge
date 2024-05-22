class NegativeFeedback:
    def __init__(self, system):
        self.fps_list = system.fps_list
        self.resolution_list = system.resolution_list
        self.buffer_size_list = system.buffer_size_list

        self.schedule_knobs = ['resolution', 'fps', 'buffer_size', 'pipeline']

    def __call__(self, latest_policy, meta_decision):
        pass
