import os
import shutil

from core.lib.estimation import TimeEstimator
from core.lib.network import http_request
from core.lib.common import LOGGER
from core.lib.common import Context
from core.lib.content import Task
from core.lib.network import get_merge_address
from core.lib.network import NodeInfo
from core.lib.network import NetworkAPIPath, NetworkAPIMethod


class Controller:
    def __init__(self):
        self.cur_task = None

        self.service_ports_dict = Context.get_parameter('service_port', direct=False)
        self.controller_port = Context.get_parameter('controller_port')
        self.distributor_port = Context.get_parameter('distributor_port')
        self.distributor_ip = NodeInfo.hostname2ip(Context.get_parameter('distributor_name'))
        self.distribute_address = get_merge_address(self.distributor_ip,
                                                    port=self.distributor_port,
                                                    path=NetworkAPIPath.DISTRIBUTOR_DISTRIBUTE)

        self.local_device = NodeInfo.get_local_device()

    def set_current_task(self, task_data: str):
        self.cur_task = Task.deserialize(task_data)

    def send_task_to_other_device(self, device):
        controller_address = get_merge_address(NodeInfo.hostname2ip(device),
                                               port=self.controller_port,
                                               path=NetworkAPIPath.CONTROLLER_TASK)

        self.record_transmit_ts(is_end=False)

        http_request(url=controller_address,
                     method=NetworkAPIMethod.CONTROLLER_TASK,
                     data={'data': Task.serialize(self.cur_task)},
                     files={'file': (self.cur_task.get_file_path(),
                                     open(self.cur_task.get_file_path(), 'rb'),
                                     'multipart/form-data')}
                     )

        LOGGER.info(f'[To Device {device}] source: {self.cur_task.get_source_id()}  '
                    f'task: {self.cur_task.get_task_id()}')

    def send_task_to_service(self, service):
        service_address = get_merge_address(NodeInfo.hostname2ip(self.local_device),
                                            port=self.service_ports_dict[service],
                                            path=NetworkAPIPath.PROCESSOR_PROCESS
                                            )

        self.record_execute_ts(is_end=False)

        http_request(url=service_address,
                     method=NetworkAPIMethod.PROCESSOR_PROCESS,
                     data={'data': Task.serialize(self.cur_task)},
                     files={'file': (self.cur_task.get_file_path(),
                                     open(self.cur_task.get_file_path(), 'rb'),
                                     'multipart/form-data')}
                     )

        LOGGER.info(f'[To Service {service}] source: {self.cur_task.get_source_id()}  '
                    f'task: {self.cur_task.get_task_id()}')

    def send_task_to_distributor(self):
        self.record_transmit_ts(is_end=False)

        http_request(url=self.distribute_address,
                     method=NetworkAPIMethod.DISTRIBUTOR_DISTRIBUTE,
                     data={'data': Task.serialize(self.cur_task)},
                     files={'file': (self.cur_task.get_file_path(),
                                     open(self.cur_task.get_file_path(), 'rb'),
                                     'multipart/form-data')}
                     )

        LOGGER.info(f'[To Distributor] source: {self.cur_task.get_source_id()}  task: {self.cur_task.get_task_id()}')

    def submit_task(self):

        assert self.cur_task, 'Current Task of Controller is Not set!'

        LOGGER.info(f'[Submit Task] source: {self.cur_task.get_source_id()}  task: {self.cur_task.get_task_id()}')

        service_name, _ = self.cur_task.get_current_service()
        dst_device = self.cur_task.get_current_stage_device()

        if service_name == 'end':
            self.send_task_to_distributor()
            action = 'transmit'
        elif dst_device != self.local_device:
            self.send_task_to_other_device(dst_device)
            action = 'transmit'
        else:
            action = 'transmit'
            self.send_task_to_service(service_name)
            action = 'execute'

        return action


    def process_return(self):
        assert self.cur_task, 'Current Task of Controller is Not set!'

        LOGGER.info(f'[Process Return] source: {self.cur_task.get_source_id()}  task: {self.cur_task.get_task_id()}')

        self.cur_task.step_to_next_stage()

    def record_transmit_ts(self, is_end: bool):
        assert self.cur_task, 'Current Task of Controller is Not set!'

        task, duration = TimeEstimator.record_pipeline_ts(self.cur_task, is_end=is_end, sub_tag='transmit')
        self.cur_task = task

        if is_end:
            self.cur_task.save_transmit_time(duration)
            LOGGER.info(f'[Source {task.get_source_id()} / Task {task.get_task_id()}] '
                        f'record transmit time of stage {task.get_flow_index()}: {duration:.3f}s')

    def record_execute_ts(self, is_end: bool):
        assert self.cur_task, 'Current Task of Controller is Not set!'

        task, duration = TimeEstimator.record_pipeline_ts(self.cur_task, is_end=is_end, sub_tag='execute')
        self.cur_task = task

        if is_end:
            self.cur_task.save_execute_time(duration)
            LOGGER.info(f'[Source {task.get_source_id()} / Task {task.get_task_id()}] '
                        f'record execute time of stage {task.get_flow_index()}: {duration:.3f}s')
