import asyncio
import copy
import json
import os
import shutil
import threading

import cv2
import uvicorn
from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form
from fastapi.routing import APIRoute
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from car_detection_trt import CarDetection

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

        self.batch_size = 8
        self.device = 0
        self.plugin_Library = Context.get_file_path('libmyplugins.so')
        self.engine_file_path = Context.get_file_path('yolov5s.engine')

        service_args = {
            'weights': self.engine_file_path,
            'plugin_library': self.plugin_Library,
            'batch_size': self.batch_size,
            'device': self.device
        }

        self.estimator = CarDetection(service_args)

        self.app.add_middleware(
            CORSMiddleware, allow_origins=["*"], allow_credentials=True,
            allow_methods=["*"], allow_headers=["*"],
        )

        self.task_queue = LocalPriorityQueue()

    def cal(self, file_path):
        content = []
        video_cap = cv2.VideoCapture(file_path)

        start = time.time()
        while True:
            ret, frame = video_cap.read()
            if not ret:
                break
            content.append(frame)
        os.remove(file_path)
        end = time.time()
        LOGGER.debug(f'decode time:{end - start}s')

        start = time.time()
        result = self.estimator(content)
        end = time.time()
        LOGGER.debug(f'process time:{end - start}s')
        assert type(result) is dict

        return result

    def deal_service(self, data, file):
        data = json.loads(data)
        source_id = data['source_id']
        task_id = data['task_id']

        tmp_path = f'tmp_receive_source_{source_id}_task_{task_id}_{time.time()}.mp4'
        with open(tmp_path, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)
            del file

        self.task_queue.put(Task(data, tmp_path))

    async def deal_request(self, backtask: BackgroundTasks, file: UploadFile = File(...), data: str = Form(...)):
        backtask.add_task(self.deal_service, data, file)
        return {'msg': 'data send success!'}

    def start_uvicorn_server(self):
        LOGGER.info(f'start uvicorn server on {9001} port')

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Configure and run the server
        config = uvicorn.Config(app=self.app, host="0.0.0.0", port=9001, log_level="debug")
        server = uvicorn.Server(config)
        loop.run_until_complete(server.serve())

    def main_loop(self):
        LOGGER.info('start main loop..')
        while True:
            if not self.task_queue.empty():
                task = self.task_queue.get()
                if task is not None:
                    source_id = task.metadata['source_id']
                    task_id = task.metadata['task_id']
                    pipeline = task.metadata['pipeline_flow']
                    tmp_data = task.metadata['tmp_data']
                    index = task.metadata['cur_flow_index']
                    scenario = task.metadata['scenario_data']
                    content = task.metadata['content_data']

                    result = self.cal(task.file_path)
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

                    http_request(url=self.controller_address, method='POST',
                                 data={'data': json.dumps(data)},
                                 files={'file': (f'tmp_{source_id}.mp4',
                                                 open(task.file_path, 'rb'),
                                                 'video/mp4')}
                                 )
                    os.remove(task.file_path)


if __name__ == '__main__':
    service_server = ServiceServer()

    threading.Thread(target=service_server.start_uvicorn_server).start()

    service_server.main_loop()
