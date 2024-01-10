import os
import shutil
import time

import cv2
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.routing import APIRoute
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from face_detection import FaceDetection

from log import LOGGER

class ServiceServer:

    def __init__(self):
        self.app = FastAPI(routes=[
            APIRoute('/predict',
                     self.cal,
                     response_class=JSONResponse,
                     methods=['POST']

                     ),
        ], log_level='trace', timeout=6000)

        self.estimator = FaceDetection({
            'net_type': 'mb_tiny_RFB_fd',
            'input_size': 480,
            'threshold': 0.7,
            'candidate_size': 1500,
            'device': 'cuda:0'
        })

        self.app.add_middleware(
            CORSMiddleware, allow_origins=["*"], allow_credentials=True,
            allow_methods=["*"], allow_headers=["*"],
        )

    async def cal(self, file: UploadFile = File(...), data: str = Form(...)):

        tmp_path = f'tmp_receive_{time.time()}.mp4'
        with open(tmp_path, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)
            del file

        content = []
        video_cap = cv2.VideoCapture(tmp_path)

        start = time.time()
        while True:
            ret, frame = video_cap.read()
            if not ret:
                break
            content.append(frame)
        os.remove(tmp_path)
        end = time.time()
        LOGGER.debug(f'decode time:{end-start}s')

        start = time.time()
        result = await self.estimator(content)
        end = time.time()
        LOGGER.debug(f'process time:{end - start}s')
        assert type(result) is dict

        return result


app_server = ServiceServer()
app = app_server.app
