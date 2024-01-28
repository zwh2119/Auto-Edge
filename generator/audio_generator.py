import copy
import json
import shutil
import wave

import cv2
import os

import requests

from utils import *
from log import LOGGER
from client import http_request
from config import Context


class AudioGenerator:
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

        self.frames_per_task = 1

        self.local_ip = get_nodes_info()[Context.get_parameters('NODE_NAME')]

    def run(self):
        cur_id = 0

        task_type, pipeline = self.get_pipeline()
        priority_single = {'importance': self.priority, 'urgency': 0, 'priority': 0}

        response = http_request(url=self.schedule_address, method='GET',
                                json={'source_id': self.generator_id,
                                      'pipeline': pipeline})

        if response is not None:
            tuned_parameters = response['plan']
            pipeline = tuned_parameters['pipeline']

        while True:
            file_path = None

            while not file_path:
                file_path = self.get_stream_data()

            LOGGER.debug(f'get an audio file from source {self.generator_id}')

            data_source = wave.open(file_path, 'r')
            nchannels, sampwidth, framerate, nframes = data_source.getparams()[:4]

            meta_data = {'source_ip': self.local_ip, 'nchannels': nchannels, 'sampwidth': sampwidth,
                         'framerate': framerate, "frames_per_task": self.frames_per_task}

            cnt = 0
            single_length = self.frames_per_task * framerate  # 4 * 8000
            while single_length * cnt < nframes:
                file_name = f'temp_{self.generator_id}_{cur_id}'

                priority = []
                for _ in range(len(pipeline) - 1):
                    temp_priority_single = copy.deepcopy(priority_single)
                    temp_priority_single['start_time'] = time.time()
                    priority.append(temp_priority_single)

                data_source.setpos(single_length * cnt)
                audio_data = data_source.readframes(min(cnt, nframes - single_length * cnt))

                with wave.open(file_name, 'w') as f:
                    f.setparams(data_source.getparams())
                    f.writeframes(audio_data)

                data = {'source_id': self.generator_id, 'task_id': cur_id, 'task_type': task_type, 'priority': priority,
                        'file_name': file_name, 'meta_data': meta_data, 'pipeline_flow': pipeline, 'tmp_data': {},
                        'cur_flow_index': 0, 'content_data': None, 'scenario_data': {}}

                # start record transmit time
                data['tmp_data'], _ = record_time(data['tmp_data'], f'transmit_time_{data["cur_flow_index"]}')

                # post task to local controller
                http_request(url=data['pipeline_flow'][data['cur_flow_index']]['execute_address'],
                             method='POST',
                             data={'data': json.dumps(data)},
                             files={'file': (file_name,
                                             open(file_name, 'rb'),
                                             'multipart/form-data')}
                             )

                os.remove(file_name)

                cur_id += 1
                cnt += 1

                os.remove(file_path)

                task_type, pipeline = self.get_pipeline()

                response = http_request(url=self.schedule_address, method='GET',
                                        json={'source_id': self.generator_id,
                                              'pipeline': pipeline})
                if response is not None:
                    tuned_parameters = response['plan']
                    pipeline = tuned_parameters['pipeline']

                time.sleep(0.5)

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

    def get_stream_data(self):
        response = http_request(url=self.data_source, no_decode=True, stream=True)
        if response:

            content_disposition = response.headers.get('content-disposition')
            file_name = content_disposition.split('filename=')[1]

            with open(file_name, 'wb') as f:
                response.raw.decode_content = True
                shutil.copyfileobj(response.raw, f)
            return file_name

        else:
            return None
