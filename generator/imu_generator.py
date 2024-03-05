import copy
import json
import shutil
import numpy as np

import cv2
import os

from utils import *
from log import LOGGER
from client import http_request
from config import Context
from scipy.signal import find_peaks
import pandas as pd


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

            LOGGER.debug(f'get an imu file from source {self.generator_id}')

            csv_data = pd.read_csv(file_path)
            start_id, end_id = self.end_point_detection(csv_data)
            num_bin = len(start_id)
            LOGGER.debug(f'num_bin:{num_bin}')
            for bi in range(num_bin):
                start_idx = int(start_id[bi])
                end_idx = int(end_id[bi]) + 1
                data = csv_data.iloc[start_idx:end_idx, [1, 6, 7, 8, 19, 20, 21]].values
                data = np.ascontiguousarray(data)

                meta_data = {'source_ip': self.local_ip}
                file_name = f'temp_{self.generator_id}_{cur_id}.npy'
                np.save(file_name, data)

                priority = []
                for _ in range(len(pipeline) - 1):
                    temp_priority_single = copy.deepcopy(priority_single)
                    temp_priority_single['start_time'] = time.time()
                    priority.append(temp_priority_single)

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

                cur_id += 1

                time.sleep(1)

            os.remove(file_path)

            task_type, pipeline = self.get_pipeline()

            response = http_request(url=self.schedule_address, method='GET',
                                    json={'source_id': self.generator_id,
                                          'pipeline': pipeline})
            if response is not None:
                tuned_parameters = response['plan']
                pipeline = tuned_parameters['pipeline']

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

    def end_point_detection(self, csv_data):
        linear_acceleration = csv_data.iloc[:, 19:22].values
        angular_velocity = csv_data.iloc[:, 6:9].values
        timestamp = csv_data.iloc[:, 1:2].values
        # transform unit
        # gyro : from deg to rad
        angular_velocity = angular_velocity / 180 * np.pi
        # linearacc: from g to m/s/s
        linear_acceleration = linear_acceleration * 9.81
        start_id, end_id = self.extractMotionLPMS3(timestamp, angular_velocity, linear_acceleration, 2)
        return start_id, end_id

    def extractMotionLPMS3(self, lpms_time, lpms_gyro, lpms_linearacc, thre):
        x1 = np.sqrt(np.sum(lpms_linearacc ** 2, axis=1))
        x2 = np.sqrt(np.sum(lpms_gyro ** 2, axis=1))
        x = x1 + 5 * x2
        wlen = 10
        inc = 5
        win = np.hanning(wlen + 2)[1:-1]
        X = self.enframe(x, win, inc)
        X = np.transpose(X)
        fn = X.shape[1]
        time = lpms_time
        id = np.arange(wlen / 2, wlen / 2 + (fn - 1) * inc + 1, inc)
        id = id - 1
        frametime = time[id.astype(int)]
        En = np.zeros(fn)

        for i in range(fn):
            u = X[:, i]
            u2 = u * u
            En[i] = np.sum(u2)
        locs, pks = find_peaks(En, height=max(En) / 20, distance=15)
        pks = pks['peak_heights']
        # initialize startend_locs
        startend_locs = np.zeros((len(locs), 2), dtype=int)
        for i in range(len(locs)):
            si = locs[i] - 1
            while si > 0:
                if En[si] < thre:
                    break
                si -= 1

            ei = locs[i] + 1
            while ei < len(En):
                if En[ei] < thre:
                    break
                ei += 1

            startend_locs[i, 0] = si
            startend_locs[i, 1] = ei

        # delete repeat points
        startend_locs = np.unique(startend_locs, axis=0)

        # get id range
        start_id = id[startend_locs[:, 0]]
        end_id = id[startend_locs[:, 1] - 1]
        return start_id, end_id

    def enframe(self, x, win, inc):
        nx = len(x)
        nwin = len(win)
        if nwin == 1:
            length = win
        else:
            length = nwin
        nf = int(np.fix((nx - length + inc) / inc))
        f = np.zeros((nf, length))
        indf = inc * np.arange(nf).reshape(-1, 1)
        inds = np.arange(1, length + 1)
        f[:] = x[indf + inds - 1]  # 对数据分帧
        if nwin > 1:
            w = win.ravel()
            f = f * w[np.newaxis, :]
        return f
