import shutil

from fastapi import FastAPI, BackgroundTasks

from fastapi.routing import APIRoute
from starlette.responses import JSONResponse
from starlette.requests import Request
from fastapi.middleware.cors import CORSMiddleware

import numpy as np
import os
import json

from utils import *
from log import LOGGER
from client import http_request
from config import Context


class DistributorServer:
    def __init__(self):
        self.app = FastAPI(routes=[
            APIRoute('/distribute',
                     self.deal_response,
                     response_class=JSONResponse,
                     methods=['POST']

                     ),
            APIRoute('/result',
                     self.query_result,
                     response_class=JSONResponse,
                     methods=['GET']
                     ),
        ], log_level='trace', timeout=6000)

        self.app.add_middleware(
            CORSMiddleware, allow_origins=["*"], allow_credentials=True,
            allow_methods=["*"], allow_headers=["*"],
        )

        self.scheduler_port = Context.get_parameters('scheduler_port')
        self.scheduler_ip = get_nodes_info()[Context.get_parameters('scheduler_name')]

        self.record_dir = Context.get_parameters('output_dir')
        if not os.path.exists(self.record_dir):
            os.makedirs(self.record_dir)
        else:
            shutil.rmtree(self.record_dir, ignore_errors=True)
            os.makedirs(self.record_dir)

        self.scheduler_address = get_merge_address(self.scheduler_ip, port=self.scheduler_port, path='scenario')

    def record_process_data(self, source_id, task_id, content_data):
        file_name = f'data_record_source_{source_id}_task_{task_id}_{int(time.time())}.json'
        file_path = os.path.join(self.record_dir, file_name)

        data = content_data

        with open(file_path, 'w') as f:
            json.dump(data, f)

    def distribute_data(self, data):
        pipeline = data['pipeline_flow']
        tmp_data = data['tmp_data']
        index = data['cur_flow_index']
        content = data['content_data']
        scenario = data['scenario_data']

        # end record transmit time
        tmp_data, transmit_time = record_time(tmp_data, f'transmit_time_{index}')
        assert transmit_time != -1
        pipeline[index]['execute_data']['transmit_time'] = transmit_time

        source_id = data['source_id']
        task_id = data['task_id']
        task_type = data['task_type']
        meta_data = data['meta_data']
        priority = data['priority']
        LOGGER.debug(f'priority info: {priority}')

        if content == 'discard':
            LOGGER.info(f'discard package: source {source_id} /task {task_id}')
            return

        num = np.mean(scenario['obj_num']) if len(scenario['obj_num']) > 1 else scenario['obj_num'][0]
        size = np.mean(scenario['obj_size']) if 'obj_size' in scenario else None

        LOGGER.info(f'source:{source_id}, task:{task_id}')

        record_data = {'source': source_id, 'task': task_id, 'task_type': task_type,
                       'obj_num': num, 'obj_size': size,
                       'pipeline': pipeline,
                       'meta_data': meta_data,
                       'priority': priority}
        self.record_process_data(source_id, task_id, record_data)

        # post scenario data to scheduler
        http_request(url=self.scheduler_address, method='POST',
                     json={'source_id': source_id, 'scenario': {'pipeline': pipeline,
                                                                'obj_num': num,
                                                                'obj_size': size,
                                                                'meta_data': meta_data}})

    async def deal_response(self, request: Request, backtask: BackgroundTasks):
        data = await request.json()
        backtask.add_task(self.distribute_data, data)
        return {'msg': 'data send success!'}

    def find_record_by_time(self, time_begin):
        file_list = []
        for file in os.listdir(self.record_dir):
            if file.startswith('data_record'):
                if int(file.split('.')[0].split('_')[6]) > time_begin:
                    file_list.append(file)
        file_list.sort(key=lambda x: int(x.split('.')[0].split('_')[6]))
        return file_list

    def extract_record(self, files):
        content = []
        for file in files:
            file_path = os.path.join(self.record_dir, file)
            with open(file_path, 'r') as f:
                content.append(json.load(f))
        return content

    async def query_result(self, request: Request):
        data = await request.json()
        files = self.find_record_by_time(data['time_ticket'])
        if len(files) > data['size']:
            files = files[:data['size']]
        return {'result': self.extract_record(files),
                'time_ticket': int(files[-1].split('.')[0].split('_')[6]) if len(files) > 0 else data['time_ticket'],
                'size': len(files)}


server = DistributorServer()
app = server.app
