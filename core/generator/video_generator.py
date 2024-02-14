from generator import Generator
from core.lib.content import Task
from core.lib.network import NodeInfo
from core.lib.network import get_merge_address
from core.lib.network import http_request
from core.lib.network import NetworkAPIPath, NetworkAPIMethod
from core.lib.common import Context
from core.lib.common import ClassType, ClassFactory


@ClassFactory.register(ClassType.GENERATOR, alias='video')
class VideoGenerator(Generator):
    def __init__(self, source_id: int, task_pipeline: list,
                 data_source: str, metadata: dict):
        super().__init__(source_id, task_pipeline)

        self.task_id = 0
        self.video_data_source = data_source
        self.raw_meta_data = metadata
        self.meta_data = metadata

        self.local_device = NodeInfo.get_local_device()
        self.task_pipeline = Task.set_execute_device(self.task_pipeline, self.local_device)

        self.scheduler_port = Context.get_parameter('scheduler_port')
        self.controller_port = Context.get_parameter('controller_port')
        self.schedule_address = get_merge_address(NodeInfo.hostname2ip(Context.get_parameter('scheduler_name')),
                                                  port=self.scheduler_port, path=NetworkAPIPath.SCHEDULER_SCHEDULE)

    def request_schedule_policy(self):
        response = http_request(url=self.schedule_address,
                                method=NetworkAPIMethod.SCHEDULER_SCHEDULE,
                                json={'source_id': self.source_id,
                                      'metadata': self.meta_data,
                                      'pipeline': Task.serialize(self.task_pipeline)})
        # TODO: make different schedule interface the same (with different parameters)
        if response is not None:
            return
        else:
            return None

    def run(self):
        while True:
            pass
