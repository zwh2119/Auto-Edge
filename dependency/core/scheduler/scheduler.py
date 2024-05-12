import threading

from core.lib.common import Context, FileNameConstant


class Scheduler:
    def __init__(self):
        self.schedule_table = {}
        self.resource_table = {}

        self.config_extraction = Context.get_algorithm('SCH_CONFIG')
        self.startup_policy = Context.get_algorithm('SCH_STARTUP')
        self.scheduler_agent = Context.get_algorithm('SCH_AGENT')

        self.extract_configuration(Context.get_file_path(FileNameConstant.SCHEDULE_CONFIG.value))

        self.run()

    def extract_configuration(self, config_path):
        self.config_extraction(self, config_path)

    def run(self):
        threading.Thread(self.scheduler_agent.run).start()

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
