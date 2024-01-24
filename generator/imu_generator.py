import copy
import json

import cv2
import os

from utils import *
from log import LOGGER
from client import http_request
from config import Context


class IMUGenerator:
    def __init__(self, data_source: str, generator_id: int, priority: int,
                 schedule_address: str, task_manage_address: str, controller_port: str):
        self.data_source = data_source
        self.data_source_capture = cv2.VideoCapture(data_source)
        self.schedule_address = schedule_address
        self.task_manage_address = task_manage_address
        self.controller_port = controller_port
        self.raw_meta_data = {}
        self.data_source = data_source
        self.generator_id = generator_id
        self.priority = priority

        self.local_ip = get_nodes_info()[Context.get_parameters('NODE_NAME')]

    def run(self):
        cur_id = 0
        cnt = 0

        task_type, pipeline = self.get_pipeline()
        priority_single = {'importance': self.priority, 'urgency': 0, 'priority': 0}

        response = http_request(url=self.schedule_address, method='GET', json={'source_id': self.generator_id,
                                                                               'pipeline': pipeline})

        if response is not None:
            tuned_parameters = response['plan']

            # priority = tuned_parameters['priority']
            pipeline = tuned_parameters['pipeline']

        update_flag = True
        while True:
            ret, frame = self.data_source_capture.read()

            # retry when no video signal
            while not ret:
                if update_flag:
                    LOGGER.warning(f'no video signal of source {self.generator_id}')
                    update_flag = False
                cnt = 0
                self.data_source_capture = cv2.VideoCapture(self.data_source)
                ret, frame = self.data_source_capture.read()

            update_flag = True

            LOGGER.debug(f'get a frame from source {self.generator_id}')
            resolution_raw = resolution2text((self.data_source_capture.get(cv2.CAP_PROP_FRAME_WIDTH),
                                              self.data_source_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
            fps_raw = self.data_source_capture.get(cv2.CAP_PROP_FPS)

            # adjust resolution
            frame = cv2.resize(frame, text2resolution(frame_resolution))

            # adjust fps
            cnt += 1
            if fps_mode == 'skip' and cnt % skip_frame_interval == 0:
                continue

            if fps_mode == 'remain' and cnt % remain_frame_interval != 0:
                continue

            # put frame in buffer
            temp_frame_buffer.append(frame)
            if len(temp_frame_buffer) < frames_per_task:
                continue
            else:
                # compress frames in the buffer into a short video
                compressed_video_pth = self.compress_frames(temp_frame_buffer, frame_fourcc)

                """
                data structure

                1.source_id
                2.task_id
                3.priority 
                4.meta_data:{resolution_raw, fps_raw, resolution, frame_number,
                            skip_interval, encoding， generate_ip}

                5.pipeline_flow:[service1, service2,..., end]
                    service:{service_name, execute_address, execute_data}
                    execute_data:{service_time, transmit_time, acc}
                6.cur_flow_index
                7.scenario_data:{obj_num, obj_size, stable}
                8.content_data (middle_result/result)
                9.tmp_data:{} (middle_record)

                """
                meta_data = {'source_ip': self.local_ip}

                priority = []
                for _ in range(len(pipeline) - 1):
                    temp_priority_single = copy.deepcopy(priority_single)
                    temp_priority_single['start_time'] = time.time()
                    priority.append(temp_priority_single)

                data = {'source_id': self.generator_id, 'task_id': cur_id, 'task_type': task_type, 'priority': priority,
                        'meta_data': meta_data, 'pipeline_flow': pipeline, 'tmp_data': {}, 'cur_flow_index': 0,
                        'content_data': None, 'scenario_data': {}}

                # start record transmit time
                data['tmp_data'], _ = record_time(data['tmp_data'], f'transmit_time_{data["cur_flow_index"]}')

                # post task to local controller
                http_request(url=data['pipeline_flow'][data['cur_flow_index']]['execute_address'],
                             method='POST',
                             data={'data': json.dumps(data)},
                             files={'file': (f'tmp_{self.generator_id}.mp4',
                                             open(compressed_video_pth, 'rb'),
                                             'video/mp4')}
                             )

                cur_id += 1
                temp_frame_buffer = []
                os.remove(compressed_video_pth)

                task_type, pipeline = self.get_pipeline()

                response = http_request(url=self.schedule_address, method='GET', json={'source_id': self.generator_id,
                                                                                       'resolution_raw': resolution_raw,
                                                                                       'fps_raw': fps_raw,
                                                                                       'pipeline': pipeline})

                if response is not None:
                    tuned_parameters = response['plan']

                    frame_resolution = tuned_parameters['resolution']
                    frame_fourcc = tuned_parameters['encoding']
                    fps = tuned_parameters['fps']
                    # priority = tuned_parameters['priority']
                    pipeline = tuned_parameters['pipeline']

                fps = min(fps, fps_raw)
                fps_mode, skip_frame_interval, remain_frame_interval = self.get_fps_adjust_mode(fps_raw, fps)

    def get_pipeline(self):
        response = http_request(url=self.task_manage_address, method='GET', json={'id': self.generator_id})
        task_type = response['task_type']
        pipeline = response['pipeline']

        pipeline.append({'service_name': 'end', 'execute_address': '', 'execute_data': {}})
        for task in pipeline:
            if task['service_name'] == 'end':
                break
            task['execute_address'] = get_merge_address(self.local_ip, port=self.controller_port, path='submit_task')
            task['execute_data'] = {}

        return task_type, pipeline
