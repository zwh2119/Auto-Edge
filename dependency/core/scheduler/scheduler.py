import time

from core.lib.common import Context, FileNameConstant, YamlOps


class Scheduler:
    def __init__(self):
        self.schedule_table = {}
        self.resource_table = {}

        config_file_path = Context.get_file_path(FileNameConstant.SCHEDULE_CONFIG.value)
        configs = YamlOps.read_yaml(config_file_path)
        self.fps_list = configs['fps']
        self.resolution_list = configs['resolution']

        self.schedule_interval = 1

    def register_schedule_table(self, source_id):
        if source_id in self.schedule_table:
            return

    def get_schedule_plan(self, info):
        return {
            'resolution': '1080p',
            'fps': 30,
            'encoding': 'mp4v',
            'batch_size': 8,
            'pipeline': info['pipeline']
        }

    def update_scheduler_scenario(self, info):
        pass

    def register_resource_table(self, device):
        if device in self.resource_table:
            return
        self.resource_table[device] = {}

    def update_scheduler_resource(self, info):
        pass

    def get_scheduler_resource(self):
        return self.resource_table

    def run(self):
        pass
