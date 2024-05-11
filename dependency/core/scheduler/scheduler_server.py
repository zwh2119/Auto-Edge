import json
import threading

from fastapi import FastAPI, Form
from fastapi.routing import APIRoute
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from core.lib.network import NetworkAPIMethod, NetworkAPIPath

from .scheduler import Scheduler


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
            APIRoute(NetworkAPIPath.SCHEDULER_POST_RESOURCE,
                     self.update_resource_state,
                     response_class=JSONResponse,
                     methods=[NetworkAPIMethod.SCHEDULER_POST_RESOURCE]
                     ),
            APIRoute(NetworkAPIPath.SCHEDULER_GET_RESOURCE,
                     self.get_resource_state,
                     response_class=JSONResponse,
                     methods=[NetworkAPIMethod.SCHEDULER_GET_RESOURCE]
                     ),
        ], log_level='trace', timeout=6000)

        self.app.add_middleware(
            CORSMiddleware, allow_origins=["*"], allow_credentials=True,
            allow_methods=["*"], allow_headers=["*"],
        )

        self.scheduler = Scheduler()
        threading.Thread(target=self.scheduler.run).start()

    async def generate_schedule_plan(self, data: str = Form(...)):
        data = json.loads(data)

        self.scheduler.register_schedule_table(data['source_id'])
        plan = self.scheduler.get_schedule_plan(data)

        return {'plan': plan}

    async def update_object_scenario(self, data: str = Form(...)):
        data = json.loads(data)

        self.scheduler.update_scheduler_scenario(data)

    async def update_resource_state(self, data: str = Form(...)):
        data = json.loads(data)

        self.scheduler.register_resource_table(data['device'])
        self.scheduler.update_scheduler_resource(data)

    async def get_resource_state(self):
        return self.scheduler.get_scheduler_resource()
