import asyncio
import copy
import json
import os
import shutil
import threading
from PIL import Image

import cv2
import uvicorn
from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form
from fastapi.routing import APIRoute
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from log import LOGGER
from config import Context
from client import http_request
from utils import *
from task_queue import LocalPriorityQueue
from task import Task

from license_plate_detection import detect


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

        self.app.add_middleware(
            CORSMiddleware, allow_origins=["*"], allow_credentials=True,
            allow_methods=["*"], allow_headers=["*"],
        )

        self.max_queue_size = eval(Context.get_parameters('max_queue_size'))
        self.task_queue = LocalPriorityQueue(max_size=self.max_queue_size)

    def cal(self, file_path, content):
        result = {}
        result['parameters'] = {}
        video_cap = cv2.VideoCapture(file_path)
        cnt = 0
        content_result = []
        content_num = []
        while True:
            ret, frame = video_cap.read()
            if not ret:
                break
            height, width, _ = frame.shape
            cur_res = []
            for x_min, y_min, x_max, y_max in content[cnt]:
                x_min = int(max(x_min, 0))
                y_min = int(max(y_min, 0))
                x_max = int(min(width, x_max))
                y_max = int(min(height, y_max))
                img = Image.fromarray(frame[y_min:y_max, x_min:x_max])

                try:
                    res = detect(img)
                except Exception as e:
                    res = None
                if res is not None:
                    cur_res.append(res)

            content_result.append(cur_res)
            content_num.append(len(cur_res))
            cnt += 1

        result['result'] = content_result
        result['parameters']['plate_num'] = content_num
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
        LOGGER.info(f'start uvicorn server on {9002} port')

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Configure and run the server
        uvicorn_config = uvicorn.Config(app=self.app, host="0.0.0.0", port=9002, log_level="debug")
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

                    result = self.cal(task.file_path, content)
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
                                 files={'file': (f'tmp_{source_id}.mp4',
                                                 open(task.file_path, 'rb'),
                                                 'video/mp4')}
                                 )
                    os.remove(task.file_path)


if __name__ == '__main__':
    service_server = ServiceServer()

    threading.Thread(target=service_server.start_uvicorn_server).start()

    service_server.main_loop()
