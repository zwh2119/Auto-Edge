import asyncio

import threading

import uvicorn
from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form
from fastapi.routing import APIRoute
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware


class ServiceServer:

    def __init__(self):
        self.app = FastAPI(routes=[
            APIRoute('/predict',
                     self.deal_request,
                     response_class=JSONResponse,
                     methods=['POST']

                     ),
        ], log_level='trace', timeout=6000)

        self.app.add_middleware(
            CORSMiddleware, allow_origins=["*"], allow_credentials=True,
            allow_methods=["*"], allow_headers=["*"],
        )

    def deal_service(self, data, file):
        print('get request')

    async def deal_request(self, backtask: BackgroundTasks, file: UploadFile = File(...), data: str = Form(...)):
        backtask.add_task(self.deal_service, data, file)
        return {'msg': 'data send success!'}

    def start_uvicorn_server(self):
        print(f'start uvicorn server on {9001} port')
        # Set up a new event loop for the thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Configure and run the server
        config = uvicorn.Config(app=self.app, host="0.0.0.0", port=9001, log_level="debug")
        server = uvicorn.Server(config)
        loop.run_until_complete(server.serve())

    def main_loop(self):
        print('start main loop..')
        while True:
            pass


def main():
    service_server = ServiceServer()

    threading.Thread(target=service_server.start_uvicorn_server).start()

    service_server.main_loop()

if __name__ == '__main__':
    main()
