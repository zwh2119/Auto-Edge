from fastapi import FastAPI, BackgroundTasks

from fastapi.routing import APIRoute
from starlette.responses import JSONResponse
from starlette.requests import Request
from fastapi.middleware.cors import CORSMiddleware

from core.lib.network import NetworkAPIPath, NetworkAPIMethod


class DistributorServer:
    def __init__(self):
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
        ], log_level='trace', timeout=6000)

        self.app.add_middleware(
            CORSMiddleware, allow_origins=["*"], allow_credentials=True,
            allow_methods=["*"], allow_headers=["*"],
        )

    async def distribute_data(self):
        pass

    def distribute_data_background(self):
        pass

    async def query_result(self):
        pass




