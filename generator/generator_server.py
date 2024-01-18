import uvicorn
from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form
from fastapi.routing import APIRoute
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio

import yaml_utils
import threading
from video_generator import VideoGenerator
from utils import *
from log import LOGGER
from config import Context


class GeneratorServer:
    def __init__(self, configs):
        self.configs = configs
        self.app = FastAPI(routes=[
            APIRoute('/task',
                     self.get_task_type,
                     response_class=JSONResponse,
                     methods=['GET']

                     ),
            APIRoute('/task',
                     self.query_new_task,
                     response_class=JSONResponse,
                     methods=['POST']

                     ),
        ], log_level='trace', timeout=6000)

        self.app.add_middleware(
            CORSMiddleware, allow_origins=["*"], allow_credentials=True,
            allow_methods=["*"], allow_headers=["*"],
        )

    def start_uvicorn_server(self):
        LOGGER.info(f'start uvicorn server on {9600} port')

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Configure and run the server
        uvicorn_config = uvicorn.Config(app=self.app, host="0.0.0.0", port=9600, log_level="debug")
        server = uvicorn.Server(uvicorn_config)
        loop.run_until_complete(server.serve())

    async def get_task_type(self, request: Request):
        data = await request.json()

    async def query_new_task(self, request: Request):
        data = await request.json()

        return {'msg': 'task submit success'}


def main():
    scheduler_path = 'schedule'
    scheduler_port = Context.get_parameters('scheduler_port')
    controller_port = Context.get_parameters('controller_port')
    scheduler_ip = get_nodes_info()[Context.get_parameters('scheduler_name')]

    video_config = yaml_utils.read_yaml(Context.get_file_path('video_config.yaml'))
    videos = video_config['video']

    server = GeneratorServer(videos)
    threading.Thread(target=server.start_uvicorn_server).start()

    scheduler_address = get_merge_address(scheduler_ip, port=scheduler_port, path=scheduler_path)
    for video in videos:
        video_generator = VideoGenerator(video['url'], video['id'], video['priority'], video['pipeline'],
                                         scheduler_address, controller_port, video['resolution'], video['fps'])
        threading.Thread(target=video_generator.run).start()


if __name__ == '__main__':
    main()
