import copy
import json

import cv2
import os

from utils import *
from log import LOGGER
from client import http_request
from config import Context


class EdgeEyeGenerator:
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

        self.buffer_size = 4
        self.encoding = 'mp4v'

        self.local_ip = get_nodes_info()[Context.get_parameters('NODE_NAME')]

    # TODO： how to process video source in real-time.
    #        currently some frames from video source
    #        will be discarded in the process of frame compress.
    def run(self):
        cur_id = 0
        cnt = 0

        task_type, pipeline = self.get_pipeline()
        priority_single = {'importance': self.priority, 'urgency': 0, 'priority': 0}

        response = http_request(url=self.schedule_address, method='GET', json={'source_id': self.generator_id,
                                                                               'pipeline': pipeline})

        if response is not None:
            tuned_parameters = response['plan']

            pipeline = tuned_parameters['pipeline']

        temp_frame_buffer = []
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
            cnt += 1

            # put frame in buffer
            temp_frame_buffer.append(frame)
            if len(temp_frame_buffer) < self.buffer_size:
                continue
            else:
                # compress frames in the buffer into a short video
                compressed_video_pth = self.compress_frames(temp_frame_buffer, self.encoding)

                meta_data = {'frame_number': self.buffer_size, 'encoding': self.encoding,
                             'source_ip': self.local_ip}

                file_name = f'temp_{self.generator_id}_{cur_id}.mp4'

                priority = []
                for _ in range(len(pipeline) - 1):
                    temp_priority_single = copy.deepcopy(priority_single)
                    temp_priority_single['start_time'] = time.time()
                    priority.append(temp_priority_single)

                data = {'source_id': self.generator_id, 'task_id': cur_id, 'task_type': task_type, 'priority': priority,
                        'file_name': file_name,
                        'meta_data': meta_data, 'pipeline_flow': pipeline, 'tmp_data': {}, 'cur_flow_index': 0,
                        'content_data': None, 'scenario_data': {}}

                # start record transmit time
                data['tmp_data'], _ = record_time(data['tmp_data'], f'transmit_time_{data["cur_flow_index"]}')

                # post task to local controller
                http_request(url=data['pipeline_flow'][data['cur_flow_index']]['execute_address'],
                             method='POST',
                             data={'data': json.dumps(data)},
                             files={'file': (file_name,
                                             open(compressed_video_pth, 'rb'),
                                             'video/mp4')}
                             )

                cur_id += 1
                temp_frame_buffer = []
                os.remove(compressed_video_pth)

                task_type, pipeline = self.get_pipeline()

                response = http_request(url=self.schedule_address, method='GET', json={'source_id': self.generator_id,
                                                                                       'pipeline': pipeline})

                if response is not None:
                    tuned_parameters = response['plan']

                    pipeline = tuned_parameters['pipeline']



    def compress_frames(self, frames, fourcc):
        fourcc = cv2.VideoWriter_fourcc(*fourcc)
        height, width, _ = frames[0].shape
        buffer_path = f'temp_{self.generator_id}.mp4'
        out = cv2.VideoWriter(buffer_path, fourcc, 30, (width, height))
        for frame in frames:
            out.write(frame)
        out.release()

        return buffer_path

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
