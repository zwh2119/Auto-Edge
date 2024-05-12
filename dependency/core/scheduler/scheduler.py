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

    def get_startup_policy(self, info):
        return self.startup_policy(info)

    def extract_scenario(self):
        pass

    def run(self):
        threading.Thread(self.scheduler_agent.run, args=(self,)).start()

    def register_schedule_table(self, source_id):
        if source_id in self.schedule_table:
            return
        self.schedule_table[source_id] = {}

    def get_schedule_plan(self, info):
        source = info['source_id']
        if 'plan' not in self.schedule_table[source]:
            return self.get_startup_policy(info)
        return self.schedule_table[source]['plan']

    def update_scheduler_scenario(self, info):
        pass

    def register_resource_table(self, device):
        if device in self.resource_table:
            return
        self.resource_table[device] = {}

    def update_scheduler_resource(self, info):
        device = info['device']
        resource = info['resource']
        self.resource_table[device] = resource

    def get_scheduler_resource(self):
        return self.resource_table
