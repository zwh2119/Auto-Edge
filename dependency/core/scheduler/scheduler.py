import threading

from core.lib.common import Context, FileNameConstant, LOGGER


class Scheduler:
    def __init__(self):
        self.schedule_table = {}
        self.resource_table = {}

        self.cloud_device = Context.get_parameter('cloud_name')

        self.config_extraction = Context.get_algorithm('SCH_CONFIG')
        self.scenario_extraction = Context.get_algorithm('SCH_SCENARIO')
        self.startup_policy = Context.get_algorithm('SCH_STARTUP')

        self.extract_configuration(Context.get_file_path(FileNameConstant.SCHEDULE_CONFIG.value))

    def extract_configuration(self, config_path):
        self.config_extraction(self, config_path)

    def get_startup_policy(self, info):
        return self.startup_policy(info)

    def add_scheduler_agent(self, source_id):
        agent = Context.get_algorithm('SCH_AGENT', system=self)
        threading.Thread(target=agent.run, args=(self,)).start()
        self.schedule_table[source_id] = agent

    def extract_scenario(self, task):
        return self.scenario_extraction(task)

    def register_schedule_table(self, source_id):
        if source_id in self.schedule_table:
            return
        self.add_scheduler_agent(source_id)

    def get_schedule_plan(self, info):
        source_id = info['source_id']
        agent = self.schedule_table[source_id]

        plan = agent.get_schedule_plan(info)

        if plan is None:
            LOGGER.debug('No schedule plan, use startup policy')
            plan = self.startup_policy(info)

        LOGGER.info(f'[Schedule Plan] Source {source_id}: {plan}')

        return plan

    def update_scheduler_scenario(self, task):
        source_id = task.get_source_id()
        if source_id not in self.schedule_table:
            LOGGER.warning(f'Scheduler agent for source {source_id} not exists!')
            return
        scenario = self.extract_scenario(task)
        agent = self.schedule_table[source_id]
        agent.update_scenario(scenario)
        LOGGER.info(f'[Update Scenario] Source {source_id}: {scenario}')

    def register_resource_table(self, device):
        if device in self.resource_table:
            return
        self.resource_table[device] = {}

    def update_scheduler_resource(self, info):
        device = info['device']
        resource = info['resource']
        self.resource_table[device] = resource

        for source_id in self.schedule_table:
            agent = self.schedule_table[source_id]
            agent.update_resource(resource)

        LOGGER.info(f'[Update Resource] Device {device}: {resource}')

    def get_scheduler_resource(self):
        return self.resource_table
