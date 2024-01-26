import asyncio
import copy
import json
import os
import shutil
import threading
import wave

import cv2
import uvicorn
from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form
from fastapi.routing import APIRoute
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from audio_classification import AudioClassification

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

        service_args = {
            'model_path': 'model.pth',
            'device': 'cpu'
        }

        self.estimator = AudioClassification(service_args)

        self.app.add_middleware(
            CORSMiddleware, allow_origins=["*"], allow_credentials=True,
            allow_methods=["*"], allow_headers=["*"],
        )

        self.task_queue = LocalPriorityQueue()

    def cal(self, file_path, task_type, metadata):
        with wave.open(file_path, 'r') as f:
            content = f.readframes(f.getnframes())

        result = self.estimator(content, metadata)

        assert type(result) is dict

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
        LOGGER.info(f'start uvicorn server on {9001} port')

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Configure and run the server
        uvicorn_config = uvicorn.Config(app=self.app, host="0.0.0.0", port=9001, log_level="debug")
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

                    result = self.cal(task.file_path, task_type, task.metadata['meta_data'])
                    if 'parameters' in result:
                        scenario.update(result['parameters'])
                    content = copy.deepcopy(result['result'])

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
