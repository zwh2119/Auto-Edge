import time

from fastapi import FastAPI, BackgroundTasks

from fastapi.routing import APIRoute
from starlette.responses import JSONResponse
from starlette.requests import Request
from fastapi.middleware.cors import CORSMiddleware

import uvicorn


class TestServer:
    def __init__(self):
        self.app = FastAPI(routes=[
            APIRoute('/test',
                     self.deal_response,
                     response_class=JSONResponse,
                     methods=['POST']

                     ),
        ], log_level='trace', timeout=6000)

        self.app.add_middleware(
            CORSMiddleware, allow_origins=["*"], allow_credentials=True,
            allow_methods=["*"], allow_headers=["*"],
        )

    def distribute_data(self, data):
        cnt = 0
        for i in range(50000000):
            cnt += i
        print(f'{data["id"]} complete:', time.time())

    async def deal_response(self, request: Request, backtask: BackgroundTasks):
        data = await request.json()
        backtask.add_task(self.distribute_data, data)
        print(f'{data["id"]} return:', time.time())
        return {'msg':'success'}


app = TestServer().app

