import asyncio
import copy
import json
import shutil

import requests
from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form

from fastapi.routing import APIRoute
from starlette.responses import JSONResponse
from starlette.requests import Request
from fastapi.middleware.cors import CORSMiddleware


class ControllerServer:
    def __init__(self):
        self.app = FastAPI(routes=[
            APIRoute('/test',
                     self.deal_response,
                     response_class=JSONResponse,
                     methods=['POST']
                     ),
        ], log_level='trace', timeout=6000)

        self.local_address = ''
        self.distribute_address = 'http://114.212.81.11:5713/distribute'

        self.app.add_middleware(
            CORSMiddleware, allow_origins=["*"], allow_credentials=True,
            allow_methods=["*"], allow_headers=["*"],
        )

    def get_params(self, file, data):
        data = json.loads(data)
        # print(data)
        # print(type(data))
        name = data['name']
        print(name)
        if name == 'file':
            with open('tmp_receive__.mp4', 'wb') as buffer:
                shutil.copyfileobj(file.file, buffer)

            print('file')
        else:
            print('no file')

    async def deal_response(self, backtask:BackgroundTasks, file: UploadFile = File(...), data: str = Form(...)):
        backtask.add_task(self.get_params, file, data)

        return {'msg': 'data send success!'}


app = ControllerServer().app
