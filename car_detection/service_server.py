import os
import shutil
import threading
import time

import cv2
import uvicorn
from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form
from fastapi.routing import APIRoute
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from car_detection_trt import CarDetection

from log import LOGGER
from config import Context
from queue import PriorityQueue
from task import Task

task_queue = PriorityQueue()


class ServiceServer:

    def __init__(self):
        self.app = FastAPI(routes=[
            APIRoute('/predict',
                     self.deal_request,
                     response_class=JSONResponse,
                     methods=['POST']

                     ),
        ], log_level='trace', timeout=6000)

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
        result = await self.estimator(content)
        end = time.time()
        LOGGER.debug(f'process time:{end - start}s')
        assert type(result) is dict

        return result

    def deal_service(self, data, file):
        tmp_path = f'tmp_receive_{time.time()}.mp4'
        with open(tmp_path, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)
            del file

    async def deal_request(self, backtask: BackgroundTasks, file: UploadFile = File(...), data: str = Form(...)):
        backtask.add_task(self.deal_service, data, file)
        return {'msg': 'data send success!'}

    def start_uvicorn_server(self):
        pass

    def main_loop(self):
        while True:
            if not task_queue.empty():
                pass


if __name__ == '__main__':
    service_server = ServiceServer()

    threading.Thread(target=service_server.start_uvicorn_server)

    service_server.main_loop()
