import json
import os

from core.lib.content import Task
from core.lib.estimation import TimeEstimator
from core.lib.common import LOGGER, FileNameConstant, Context
from core.lib.network import http_request, NodeInfo, get_merge_address, NetworkAPIMethod, NetworkAPIPath


class Distributor:
    def __init__(self):
        self.cur_task = None

        self.scheduler_ip = NodeInfo.hostname2ip(Context.get_parameter('scheduler_name'))
        self.scheduler_port = Context.get_parameter('scheduler_port')
        self.scheduler_address = self.distribute_address = get_merge_address(self.scheduler_ip,
                                                                             port=self.scheduler_port,
                                                                             path=NetworkAPIPath.SCHEDULER_SCENARIO)

    def set_current_task(self, task_data: dict):
        self.cur_task = Task.deserialize(task_data)

    def distribute_data(self):
        assert self.cur_task, 'Current Task of Controller is Not set!'

        LOGGER.info(f'[Distribute Data] source: {self.cur_task.get_source_id()}  task: {self.cur_task.get_task_id()}')

        self.save_task_record()
        self.send_scenario_to_scheduler()

    def save_task_record(self):
        record_file_name = f'record_source_{self.cur_task.get_source_id()}_task_{self.cur_task.get_task_id()}.json'
        record_path = os.path.join(FileNameConstant.DISTRIBUTE_RECORD_DIR.value, record_file_name)

        if not os.path.exists(os.path.dirname(record_path)):
            os.mkdir(os.path.dirname(record_path))

        with open(record_path, 'w') as f:
            json.dump(Task.serialize(self.cur_task), f)

    def send_scenario_to_scheduler(self):
        LOGGER.info(f'[Send Scenario] source: {self.cur_task.get_source_id()}  task: {self.cur_task.get_task_id()}')

        http_request(url=self.scheduler_address,
                     method=NetworkAPIMethod.SCHEDULER_SCENARIO,
                     data={'data': self.cur_task.get_scenario_data()})

    def record_transmit_ts(self):
        assert self.cur_task, 'Current Task of Distributor is Not set!'

        task, duration = TimeEstimator.record_pipeline_ts(self.cur_task, is_end=True, sub_tag='transmit')
        self.cur_task = task

        self.cur_task.save_transmit_time(duration)
        LOGGER.info(f'[Source {task.get_source_id()} / Task {task.get_task_id()}] '
                    f'record transmit time of stage {task.get_flow_index()}: {duration:.3f}s')
