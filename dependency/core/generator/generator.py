import json

from core.lib.common import Context
from core.lib.content import Task
from core.lib.network import get_merge_address
from core.lib.network import NodeInfo
from core.lib.network import NetworkAPIPath, NetworkAPIMethod
from core.lib.network import http_request
from core.lib.estimation import TimeEstimator
from core.lib.common import LOGGER


class Generator:
    def __init__(self, source_id: int, task_pipeline: list, metadata: dict):
        self.current_task = None

        self.source_id = source_id
        print(f'task pipeline list:{task_pipeline}')
        self.task_pipeline = Task.extract_pipeline_from_dict(task_pipeline)
        print(f'pipeline generate:{self.task_pipeline}')

        self.raw_meta_data = metadata
        self.meta_data = metadata

        self.task_content = None

        self.local_device = NodeInfo.get_local_device()
        self.task_pipeline = Task.set_execute_device(self.task_pipeline, self.local_device)

        self.scheduler_port = Context.get_parameter('scheduler_port')
        self.controller_port = Context.get_parameter('controller_port')
        self.schedule_address = get_merge_address(NodeInfo.hostname2ip(Context.get_parameter('scheduler_name')),
                                                  port=self.scheduler_port, path=NetworkAPIPath.SCHEDULER_SCHEDULE)

        self.before_schedule_operation = Context.get_algorithm('GEN_BSO')
        self.after_schedule_operation = Context.get_algorithm('GEN_ASO')

    def request_schedule_policy(self):
        params = self.before_schedule_operation(self)
        response = http_request(url=self.schedule_address,
                                method=NetworkAPIMethod.SCHEDULER_SCHEDULE,
                                data={'data': json.dumps(params)})
        self.after_schedule_operation(self, response)

    def record_total_start_ts(self):
        self.current_task, _ = TimeEstimator.record_task_ts(self.current_task,
                                                            'total_start_time',
                                                            is_end=False)

    def record_transmit_start_ts(self):
        self.current_task, _ = TimeEstimator.record_pipeline_ts(self.current_task,
                                                                is_end=False,
                                                                sub_tag='transmit')

    def submit_task_to_controller(self, compressed_file):
        assert self.current_task, 'Task is empty when submit to controller!'

        dst_device = self.current_task.get_current_stage_device()
        controller_ip = NodeInfo.hostname2ip(dst_device)
        controller_address = get_merge_address(controller_ip,
                                               port=self.controller_port,
                                               path=NetworkAPIPath.CONTROLLER_TASK)
        self.record_transmit_start_ts()
        http_request(url=controller_address,
                     method=NetworkAPIMethod.CONTROLLER_TASK,
                     data={'data': Task.serialize(self.current_task)},
                     files={'file': (self.current_task.get_file_path(),
                                     open(self.current_task.get_file_path(), 'rb'),
                                     'multipart/form-data')}
                     )
        LOGGER.info(f'[To Controller {dst_device}] source: {self.current_task.get_source_id()}  '
                    f'task: {self.current_task.get_task_id()}')

    def run(self):
        assert None, 'Base Generator should not be invoked directly!'
