import json

from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form

from fastapi.routing import APIRoute
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from core.lib.network import NetworkAPIPath, NetworkAPIMethod
from core.lib.common import Context


class ProcessorServer:
    def __init__(self):
        self.app = FastAPI(routes=[
            APIRoute(NetworkAPIPath.PROCESSOR_PROCESS,
                     self.process_service,
                     response_class=JSONResponse,
                     methods=[NetworkAPIMethod.PROCESSOR_PROCESS]
                     ),
        ], log_level='trace', timeout=6000)

        self.app.add_middleware(
            CORSMiddleware, allow_origins=["*"], allow_credentials=True,
            allow_methods=["*"], allow_headers=["*"],
        )

        self.processor = Context.get_algorithm('PRO_DETECTOR')

    def process_service(self, backtask: BackgroundTasks, file: UploadFile = File(...), data: str = Form(...)):
        file_data = await file.read()
        data = json.loads(data)
        backtask.add_task(self.process_service_background, data, file_data)

    def process_service_background(self, data, file_data):
        pass

    def start_processor_server(self):
        pass

    def loop_process(self):
        pass
