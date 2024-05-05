from fastapi import FastAPI, BackgroundTasks
from fastapi.routing import APIRoute
from starlette.responses import JSONResponse
from starlette.requests import Request
from fastapi.middleware.cors import CORSMiddleware

from core.lib.network import NetworkAPIMethod, NetworkAPIPath


class SchedulerServer:
    def __init__(self):
        self.app = FastAPI(routes=[
            APIRoute(NetworkAPIPath.SCHEDULER_SCHEDULE,
                     self.generate_schedule_plan,
                     response_class=JSONResponse,
                     methods=[NetworkAPIMethod.SCHEDULER_SCHEDULE]
                     ),
            APIRoute(NetworkAPIPath.SCHEDULER_SCENARIO,
                     self.update_object_scenario,
                     response_class=JSONResponse,
                     methods=[NetworkAPIMethod.SCHEDULER_SCENARIO]
                     ),
            APIRoute(NetworkAPIPath.SCHEDULER_RESOURCE,
                     self.update_resource_state,
                     response_class=JSONResponse,
                     methods=[NetworkAPIMethod.SCHEDULER_RESOURCE]
                     ),
        ], log_level='trace', timeout=6000)

        self.app.add_middleware(
            CORSMiddleware, allow_origins=["*"], allow_credentials=True,
            allow_methods=["*"], allow_headers=["*"],
        )

    async def generate_schedule_plan(self):
        pass

    async def update_object_scenario(self):
        pass

    async def update_resource_state(self):
        pass
