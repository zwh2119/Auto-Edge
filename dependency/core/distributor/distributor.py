import json
import os

from core.lib.content import Task
from core.lib.estimation import TimeEstimator
from core.lib.common import LOGGER, FileNameConstant, Context, FileOps
from core.lib.network import http_request, NodeInfo, get_merge_address, NetworkAPIMethod, NetworkAPIPath


class Distributor:
    def __init__(self):
        self.cur_task = None

        self.scheduler_ip = NodeInfo.hostname2ip(Context.get_parameter('scheduler_name'))
        self.scheduler_port = Context.get_parameter('scheduler_port')
        self.scheduler_address = self.distribute_address = get_merge_address(self.scheduler_ip,
                                                                             port=self.scheduler_port,
                                                                             path=NetworkAPIPath.SCHEDULER_SCENARIO)

    def set_current_task(self, task_data):
        self.cur_task = Task.deserialize(task_data)

    def distribute_data(self):
        assert self.cur_task, 'Current Task of Controller is Not set!'

        LOGGER.info(f'[Distribute Data] source: {self.cur_task.get_source_id()}  task: {self.cur_task.get_task_id()}')

        self.save_task_record()
        self.send_scenario_to_scheduler()

    def save_task_record(self):
        record_file_name = f'record_source_{self.cur_task.get_source_id()}_task_{self.cur_task.get_task_id()}.json'
        record_path = os.path.join(FileNameConstant.DISTRIBUTE_RECORD_DIR.value, record_file_name)

        FileOps.create_directory(os.path.dirname(record_path))

        with open(record_path, 'w') as f:
            f.write(Task.serialize(self.cur_task))

    def send_scenario_to_scheduler(self):
        LOGGER.info(f'[Send Scenario] source: {self.cur_task.get_source_id()}  task: {self.cur_task.get_task_id()}')
        http_request(url=self.scheduler_address,
                     method=NetworkAPIMethod.SCHEDULER_SCENARIO,
                     data={'data': Task.serialize(self.cur_task)})

    def record_transmit_ts(self):
        assert self.cur_task, 'Current Task of Distributor is Not set!'

        task, duration = TimeEstimator.record_pipeline_ts(self.cur_task, is_end=True, sub_tag='transmit')
        self.cur_task = task

        self.cur_task.save_transmit_time(duration)
        LOGGER.info(f'[Source {task.get_source_id()} / Task {task.get_task_id()}] '
                    f'record transmit time of stage {task.get_flow_index()}: {duration:.3f}s')

    def query_result(self, time_ticket, size):
        files = self.find_record_by_time(time_ticket)
        if size != 0 and len(files) > size:
            files = files[:size]

        if len(files) > 0:
            new_time_ticket = os.path.getctime(files[-1])
        else:
            new_time_ticket = time_ticket
        LOGGER.debug(f'last file time: {new_time_ticket}')

        return {'result': self.extract_record(files),
                'time_ticket': new_time_ticket,
                'size': len(files)
                }

    @staticmethod
    def find_record_by_time(time_begin):
        file_list = []
        dir_path = FileNameConstant.DISTRIBUTE_RECORD_DIR.value
        if not os.path.exists(dir_path):
            return file_list
        for file in os.listdir(dir_path):
            file_path = os.path.join(dir_path, file)
            if file.startswith('record') and os.path.getctime(file_path) > time_begin:
                LOGGER.debug(f'name:{file}  time:{os.path.getctime(file_path)}')
                file_list.append(file_path)
        file_list.sort(key=lambda x: os.path.getctime(x))
        return file_list

    @staticmethod
    def extract_record(files):
        content = []
        for file_path in files:
            with open(file_path, 'r') as f:
                content.append(f.read())
            FileOps.remove_file(file_path)
        return content
