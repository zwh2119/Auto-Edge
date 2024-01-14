import threading

from fastapi import FastAPI, BackgroundTasks

from fastapi.routing import APIRoute
from starlette.responses import JSONResponse
from starlette.requests import Request
from fastapi.middleware.cors import CORSMiddleware

from priority_schedule import *

from .scheduler import Scheduler


class ScheduleServer:
    def __init__(self):
        self.app = FastAPI(routes=[
            APIRoute('/schedule',
                     self.generate_schedule_plan,
                     response_class=JSONResponse,
                     methods=['GET']
                     ),
            APIRoute('/scenario',
                     self.deal_response,
                     response_class=JSONResponse,
                     methods=['POST']
                     ),
            APIRoute('/resource',
                     self.update_resource_state,
                     response_class=JSONResponse,
                     methods=['POST']
                     ),
            APIRoute('/priority',
                     self.generate_task_priority,
                     response_class=JSONResponse,
                     methods=['GET']
                     )
        ], log_level='trace', timeout=6000)

        self.app.add_middleware(
            CORSMiddleware, allow_origins=["*"], allow_credentials=True,
            allow_methods=["*"], allow_headers=["*"],
        )

        self.scheduler = Scheduler()

        threading.Thread(target=self.scheduler.run).start()

    async def generate_schedule_plan(self, request: Request):
        data = await request.json()
        source_id = data['source_id']
        self.scheduler.register_schedule_table(source_id)

        plan = self.scheduler.get_schedule_plan(data)

        return {'plan': plan}

    async def generate_task_priority(self, request: Request):
        data = await request.json()
        return get_task_priority(data)

    async def update_resource_state(self, request: Request):
        data = await request.json()
        device = data['device']
        resource_data = data['resource']
        self.scheduler.update_scheduler_resource(device, resource_data)

    def update_scenario(self, data):
        self.scheduler.update_scheduler_scenario(data['source_id'], data['scenario'])

    async def deal_response(self, request: Request, backtask: BackgroundTasks):
        data = await request.json()
        backtask.add_task(self.update_scenario, data)
        return {'msg': 'scheduler scenario update successfully!'}


app = ScheduleServer().app
