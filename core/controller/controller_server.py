import json

from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form

from fastapi.routing import APIRoute
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from core.lib.common import Context
from core.lib.content import Task
from core.lib.network import get_merge_address
from core.lib.network import NodeInfo
from core.lib.network import NetworkAPIPath, NetworkAPIMethod
from core.lib.network import http_request

from controller import Controller


class ControllerServer:
    def __init__(self):
        self.controller = Controller()

        self.app = FastAPI(routes=[
            APIRoute(NetworkAPIPath.CONTROLLER_TASK,
                     self.submit_task,
                     response_class=JSONResponse,
                     methods=[NetworkAPIMethod.CONTROLLER_TASK]
                     ),
        ], log_level='trace', timeout=6000)

        self.app.add_middleware(
            CORSMiddleware, allow_origins=["*"], allow_credentials=True,
            allow_methods=["*"], allow_headers=["*"],
        )

        self.service_ports_dict = Context.get_parameter('service_port', direct=False)
        self.distributor_port = Context.get_parameter('distributor_port')
        self.distributor_ip = NodeInfo.hostname2ip(Context.get_parameter('distributor_name'))
        self.distribute_address = get_merge_address(self.distributor_ip,
                                                    port=self.distributor_port,
                                                    path=NetworkAPIPath.DISTRIBUTOR_DISTRIBUTE)

        self.local_device = NodeInfo.get_local_device()

    async def submit_task(self, backtask: BackgroundTasks, file: UploadFile = File(...), data: str = Form(...)):
        file_data = await file.read()
        data = json.loads(data)
        backtask.add_task(self.submit_task_background, data, file_data)

    def submit_task_background(self, data, file_data):
        pass


app = ControllerServer().app
