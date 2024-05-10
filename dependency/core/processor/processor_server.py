import json
import asyncio
import uvicorn
from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form

from fastapi.routing import APIRoute
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from core.lib.common import Context
from core.lib.common import LOGGER, FileOps
from core.lib.network import NodeInfo, http_request, get_merge_address, NetworkAPIMethod, NetworkAPIPath
from core.lib.content import Task


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

        processor_type = Context.get_parameter('processor_type')
        self.processor = Context.get_algorithm(processor_type)

        self.task_queue = Context.get_algorithm('PRO_QUEUE')

        self.local_device = NodeInfo.get_local_device()
        self.processor_port = Context.get_parameter('processor_inner_port')
        self.controller_port = Context.get_parameter('controller_port')
        self.controller_address = get_merge_address(NodeInfo.hostname2ip(self.local_device),
                                                    port=self.controller_port,
                                                    path=NetworkAPIPath.CONTROLLER_RETURN)

    async def process_service(self, backtask: BackgroundTasks, file: UploadFile = File(...), data: str = Form(...)):
        file_data = await file.read()
        cur_task = Task.deserialize(data)
        backtask.add_task(self.process_service_background, data, file_data)
        LOGGER.debug(f'[Monitor Task] (Process Request) Source: {cur_task.get_source_id()} / Task: {cur_task.get_task_id()} ')

    def process_service_background(self, data, file_data):
        cur_task = Task.deserialize(data)
        FileOps.save_data_file(cur_task, file_data)
        self.task_queue.put(cur_task)
        LOGGER.debug(f'[Task Queue] Queue Size (receive request): {self.task_queue.size()}')
        LOGGER.debug(f'[Monitor Task] (Process Request Background) Source: {cur_task.get_source_id()} / Task: {cur_task.get_task_id()} ')

    def start_processor_server(self):
        LOGGER.info(f'start uvicorn server on {self.processor_port} port')

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Configure and run the server
        uvicorn_config = uvicorn.Config(app=self.app, host="0.0.0.0", port=int(self.processor_port), log_level="debug")
        server = uvicorn.Server(uvicorn_config)
        loop.run_until_complete(server.serve())

    def loop_process(self):
        LOGGER.info('start processing loop..')
        while True:
            if self.task_queue.empty():
                continue
            task = self.task_queue.get()
            if not task:
                continue

            LOGGER.debug(f'[Task Queue] Queue Size (loop): {self.task_queue.size()}')
            LOGGER.debug(f'[Monitor Task] (Loop Process) Source: {task.get_source_id()} / Task: {task.get_task_id()} ')

            task = self.processor(task)
            self.send_result_back_to_controller(task)
            FileOps.remove_data_file(task)

    def send_result_back_to_controller(self, task):
        LOGGER.debug(f'[Monitor Task] (Send Back) Source: {task.get_source_id()} / Task: {task.get_task_id()} ')

        http_request(url=self.controller_address, method=NetworkAPIMethod.CONTROLLER_RETURN,
                     data={'data': Task.serialize(task)},
                     files={'file': (task.get_file_path(),
                                     open(task.get_file_path(), 'rb'),
                                     'multipart/form-data')})
