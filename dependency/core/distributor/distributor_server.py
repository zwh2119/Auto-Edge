import json
import os

from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form
from fastapi.routing import APIRoute
from starlette.responses import JSONResponse, FileResponse
from starlette.requests import Request
from fastapi.middleware.cors import CORSMiddleware

from core.lib.network import NetworkAPIPath, NetworkAPIMethod
from core.lib.common import FileOps
from .distributor import Distributor


class DistributorServer:
    def __init__(self):
        self.distributor = Distributor()

        self.app = FastAPI(routes=[
            APIRoute(NetworkAPIPath.DISTRIBUTOR_DISTRIBUTE,
                     self.distribute_data,
                     response_class=JSONResponse,
                     methods=[NetworkAPIMethod.DISTRIBUTOR_DISTRIBUTE]

                     ),
            APIRoute(NetworkAPIPath.DISTRIBUTOR_RESULT,
                     self.query_result,
                     response_class=JSONResponse,
                     methods=[NetworkAPIMethod.DISTRIBUTOR_RESULT]
                     ),
            APIRoute(NetworkAPIPath.DISTRIBUTOR_FILE,
                     self.download_file,
                     response_class=JSONResponse,
                     methods=[NetworkAPIMethod.DISTRIBUTOR_FILE]
                     ),
        ], log_level='trace', timeout=6000)

        self.app.add_middleware(
            CORSMiddleware, allow_origins=["*"], allow_credentials=True,
            allow_methods=["*"], allow_headers=["*"],
        )

    async def distribute_data(self, backtask: BackgroundTasks, file: UploadFile = File(...), data: str = Form(...)):
        file_data = await file.read()
        backtask.add_task(self.distribute_data_background, data, file_data)

    def distribute_data_background(self, data, file_data):
        self.distributor.set_current_task(data)
        FileOps.save_data_file(self.distributor.cur_task, file_data)
        self.distributor.record_transmit_ts()
        self.distributor.distribute_data()

        # FileOps.remove_data_file(self.distributor.cur_task)

    async def query_result(self, request: Request):
        data = await request.json()
        size = data['size']
        time_ticket = data['time_ticket']
        return self.distributor.query_result(time_ticket, size)

    async def download_file(self, request: Request):
        data = await request.json()
        file_path = data['file']
        if os.path.exists(file_path):
            task = BackgroundTasks()
            task.add_task(FileOps.remove_file, file_path)
        return FileResponse(path=file_path,
                            filename=file_path)


