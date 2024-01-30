import asyncio
import copy
import json
import os

import threading
import numpy as np

import uvicorn
from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form
from fastapi.routing import APIRoute
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from service_processor_3 import ServiceProcessor3

from log import LOGGER
from config import Context
from client import http_request
from utils import *
from task_queue import LocalPriorityQueue
from task import Task


class ServiceServer:

    def __init__(self):
        self.app = FastAPI(routes=[
            APIRoute('/predict',
                     self.deal_request,
                     response_class=JSONResponse,
                     methods=['POST']

                     ),
        ], log_level='trace', timeout=6000)

        node_info = get_nodes_info()
        self.local_ip = node_info[Context.get_parameters('NODE_NAME')]
        self.controller_port = Context.get_parameters('controller_port')
        self.controller_address = get_merge_address(self.local_ip, port=self.controller_port, path='submit_task')

        self.distributor_ip = node_info[Context.get_parameters('distributor_name')]
        self.distributor_port = Context.get_parameters('distributor_port')
        self.distributor_address = get_merge_address(self.distributor_ip, port=self.distributor_port, path='redis')

        self.estimator = ServiceProcessor3()

        self.app.add_middleware(
            CORSMiddleware, allow_origins=["*"], allow_credentials=True,
            allow_methods=["*"], allow_headers=["*"],
        )

        self.task_queue = LocalPriorityQueue()

    def cal(self, content, redis_address):

        result = self.estimator(content, redis_address)

        return result

    def deal_service(self, data, file_data):
        LOGGER.debug('receive task from controller')
        data = json.loads(data)
        source_id = data['source_id']
        task_id = data['task_id']

        tmp_path = f'tmp_receive_source_{source_id}_task_{task_id}_{time.time()}.mp4'
        with open(tmp_path, 'wb') as buffer:
            buffer.write(file_data)

        self.task_queue.put(Task(data, tmp_path))

    async def deal_request(self, backtask: BackgroundTasks, file: UploadFile = File(...), data: str = Form(...)):
        file_data = await file.read()
        backtask.add_task(self.deal_service, data, file_data)
        return {'msg': 'data send success!'}

    def start_uvicorn_server(self):
        LOGGER.info(f'start uvicorn server on {9008} port')

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Configure and run the server
        uvicorn_config = uvicorn.Config(app=self.app, host="0.0.0.0", port=9008, log_level="debug")
        server = uvicorn.Server(uvicorn_config)
        loop.run_until_complete(server.serve())

    def main_loop(self):
        LOGGER.info('start main loop..')
        while True:
            if not self.task_queue.empty():
                LOGGER.debug('get task input from queue')
                task = self.task_queue.get()
                if task is not None:
                    source_id = task.metadata['source_id']
                    task_id = task.metadata['task_id']
                    pipeline = task.metadata['pipeline_flow']
                    tmp_data = task.metadata['tmp_data']
                    index = task.metadata['cur_flow_index']
                    scenario = task.metadata['scenario_data']
                    content = task.metadata['content_data']
                    task_type = task.metadata['task_type']

                    result = self.cal(content, self.distributor_address)
                    content = copy.deepcopy(result)

                    lps_list = []
                    rps_list = []
                    for output_ctx in result:
                        if 'lps' in lps_list:
                            lps_list.append(output_ctx['lps'])
                        else:
                            lps_list.append(0)
                        if 'rps' in rps_list:
                            rps_list.append(output_ctx['rps'])
                        else:
                            rps_list.append(0)
                    scenario.update({'obj_num': f'左：{np.mean(lps_list)}   右：{np.mean(rps_list)}'})

                    # end record service time
                    tmp_data, service_time = record_time(tmp_data, f'service_time_{index}')
                    assert service_time != -1
                    pipeline[index]['execute_data']['service_time'] = service_time
                    LOGGER.debug(f'service_time of {source_id}:{service_time}s')

                    index += 1

                    data = task.metadata
                    data['pipeline_flow'] = pipeline
                    data['tmp_data'] = tmp_data
                    data['cur_flow_index'] = index
                    data['content_data'] = content
                    data['scenario_data'] = scenario

                    LOGGER.debug('post task back to controller')

                    http_request(url=self.controller_address, method='POST',
                                 data={'data': json.dumps(data)},
                                 files={'file': (data['file_name'],
                                                 open(task.file_path, 'rb'),
                                                 'multipart/form-data')}
                                 )
                    os.remove(task.file_path)


if __name__ == '__main__':
    service_server = ServiceServer()

    threading.Thread(target=service_server.start_uvicorn_server).start()

    service_server.main_loop()
