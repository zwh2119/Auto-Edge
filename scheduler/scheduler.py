"""
scheduling parameters

resolution
fps
encoding
pipeline[{execute_address}, {execute_address}]
priority
"""
from pid import PIDController
from utils import *

from log import LOGGER
from config import Context
from yaml_utils import *


class Scheduler:
    def __init__(self):

        self.user_constraint = eval(Context.get_parameters('user_constraint'))
        self.controller_port = Context.get_parameters('controller_port')

        schedule_config = read_yaml(Context.get_file_path('schedule_config.yaml'))
        self.resolution_list = schedule_config['resolution']
        self.fps_list = schedule_config['fps']

        self.schedule_table = {}
        self.resource_table = {}

        self.schedule_interval = 1

        self.computing_devices = get_nodes_info()

        self.ip_dict = {}
        self.address_dict = {}
        for device_name in self.computing_devices:
            self.ip_dict[device_name] = self.computing_devices[device_name]
            self.address_dict[device_name] = get_merge_address(self.computing_devices[device_name],
                                                               port=self.controller_port,
                                                               path='submit_task')

        self.address_diverse_dict = {v: k for k, v in self.address_dict.items()}

    def register_schedule_table(self, source_id):
        if source_id in self.schedule_table:
            return
        self.schedule_table[source_id] = {}
        pid = PIDController()
        pid.set_setpoint(self.user_constraint)
        self.schedule_table[source_id]['pid'] = pid

    def get_schedule_plan(self, info):
        source_id = info['source_id']
        if 'plan' not in self.schedule_table[source_id]:
            return self.get_cold_start_plan(info)
        return self.schedule_table[source_id]['plan']

    def update_scheduler_scenario(self, source_id, scenario_data):
        if source_id not in self.schedule_table:
            raise Exception(f'illegal source id of {source_id}')
        self.schedule_table[source_id]['scenario'] = scenario_data

    def register_resource_table(self, device):
        if device in self.resource_table:
            return
        self.resource_table[device] = {}

    def update_scheduler_resource(self, device, resource_data):
        self.register_resource_table(device)
        self.resource_table[device] = resource_data

    def get_device_resource(self, device):
        if device not in self.resource_table:
            LOGGER.warning(f'device of {device} not exists!')
            return

        return self.resource_table[device]

    def get_cold_start_plan(self, info):
        cold_plan = {
            'resolution': '720p',
            'fps': 20,
            'encoding': 'mp4v',
            'priority': 0,
            'pipeline': info['pipeline']
        }
        return cold_plan

    def run(self):
        while True:
            LOGGER.debug('update schedule')
            for source_id in self.schedule_table:
                task_schedule = self.schedule_table[source_id]

                if 'scenario' not in task_schedule:
                    continue

                scenario = task_schedule['scenario']
                del task_schedule['scenario']

                pid = task_schedule['pid']
                pipeline = scenario['pipeline']
                meta_data = scenario['meta_data']

                latency = self.calculate_latency(pipeline)
                latency = self.finetune_real_frame_latency(latency, meta_data)
                pid_out = pid.update(latency)

                plan = self.adjust_plan_configuration(pid_out, meta_data, pipeline)
                task_schedule['plan'] = plan
                LOGGER.info(f'id:{source_id} latency:{latency} pid:{pid_out} plan:{plan}')

            # schedule interval
            time.sleep(self.schedule_interval)

    def adjust_plan_configuration(self, pid_out, meta_data, pipeline):
        position = self.map_pipeline_2_position(pipeline)
        resolution = meta_data['resolution']
        fps = round(meta_data['fps'])
        resolution_raw = meta_data['resolution_raw']
        fps_raw = round(meta_data['fps_raw'])

        source_device = self.address_diverse_dict[get_merge_address(meta_data['source_ip'], port=self.controller_port,
                                                                    path='submit_task')]

        done = False
        if pid_out > 0:

            if pid_out > 1:
                fps, done = self.change_single_configuration(self.fps_list, 1, fps, fps_raw)
            if pid_out > 2 or not done:
                resolution, done = self.change_single_configuration(self.resolution_list, 1, resolution, resolution_raw)
            if pid_out > 3 or not done:
                position, done = self.change_position(position, source_device, 1)
        if pid_out < 0:
            if pid_out < -3 or not done:
                position, done = self.change_position(position, source_device, -1)
            if pid_out < -2 or not done:
                resolution, done = self.change_single_configuration(self.resolution_list, -1, resolution,
                                                                    resolution_raw)
            if pid_out < -1:
                fps, done = self.change_single_configuration(self.fps_list, -1, fps, fps_raw)

        return {
            'resolution': resolution,
            'fps': fps,
            'encoding': 'mp4v',
            'priority': 0,
            'pipeline': self.map_position_2_pipeline(position, pipeline)
        }

    def change_position(self, position, source_position, direction):
        done = False
        if direction < 0:
            for i in range(len(position) - 1, -1, -1):
                if position[i] == source_position:
                    position[i] = 'cloud.kubeedge'
                    done = True
                    break
        else:
            for i in range(len(position)):
                if position[i] == 'cloud.kubeedge':
                    position[i] = source_position
                    done = True
                    break
        return position, done

    def change_single_configuration(self, config_list: list, direction, cur_config, max_config=None):
        cur_index = config_list.index(cur_config)
        max_index = config_list.index(max_config) if max_config is not None else len(config_list) - 1
        min_index = 0
        new_index = cur_index + direction
        new_index = max(new_index, min_index)
        new_index = min(new_index, max_index)

        return config_list[new_index], new_index != cur_index

    def calculate_latency(self, pipeline):
        latency = 0
        for task in pipeline:
            latency += task['execute_data']['transmit_time']
            if task['service_name'] != 'end':
                latency += task['execute_data']['service_time']
        return latency

    # TODO: rethink the role of fps
    def finetune_real_frame_latency(self, latency, meta_data):
        fps = meta_data['fps']
        fps_raw = meta_data['fps_raw']
        buffer_size = meta_data['frame_number']
        # return latency / int(buffer_size * fps_raw / fps)
        return latency

    def map_pipeline_2_position(self, pipeline):
        position = []
        for task in pipeline:
            if task['service_name'] == 'end':
                break

            position.append(self.address_diverse_dict[task['execute_address']])

        return position

    def map_position_2_pipeline(self, position, pipeline):
        assert len(position) + 1 == len(pipeline)
        for i, pos in enumerate(position):
            pipeline[i]['execute_address'] = self.address_dict[pos]

        return pipeline
