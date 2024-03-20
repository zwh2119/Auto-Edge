import json

from core.lib.common import Context
from core.lib.content import Task
from core.lib.network import get_merge_address
from core.lib.network import NodeInfo
from core.lib.network import NetworkAPIPath, NetworkAPIMethod
from core.lib.network import http_request


class Generator:
    def __init__(self, source_id: int, task_pipeline: list, metadata: dict):
        self.current_task = None

        self.source_id = source_id
        self.task_pipeline = Task.extract_pipeline(task_pipeline)

        self.raw_meta_data = metadata
        self.meta_data = metadata

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

    def submit_task_to_controller(self):
        assert self.current_task, 'Task is empty when submit to controller!'

        controller_ip = NodeInfo.hostname2ip(controller_host)
        controller_address = get_merge_address(controller_ip,
                                               port=self.controller_port,
                                               path=NetworkAPIPath.CONTROLLER_TASK)
        response = http_request(url=controller_address,
                                method=NetworkAPIMethod.CONTROLLER_TASK,
                                data={'data': Task.serialize(self.current_task)},
                                files={'file': (f'tmp_{self.generator_id}.mp4',
                                                open(compressed_video_pth, 'rb'),
                                                'multipart/form-data')}
                                )

    def run(self):
        assert None, 'Base Generator should not be invoked directly!'
