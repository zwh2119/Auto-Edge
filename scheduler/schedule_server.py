import threading

from fastapi import FastAPI, BackgroundTasks

from fastapi.routing import APIRoute
from starlette.responses import JSONResponse
from starlette.requests import Request
from fastapi.middleware.cors import CORSMiddleware

from task_schedule import Scheduler


class ScheduleServer:
    def __init__(self):

        self.configs = {}
        self.default_task_type = None
        self.task_counter = {}

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
                     ),
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
            APIRoute('/config',
                     self.register_new_config,
                     response_class=JSONResponse,
                     methods=['POST']
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
        return {'priority': self.scheduler.get_task_priority(data)}

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

    async def register_new_config(self, request: Request):
        data = await request.json()
        configs = data['config']

        task_types = configs[0]['task_type']
        for task_type in task_types:
            self.configs[task_type['type_name']] = task_type
            if task_type['default']:
                self.default_task_type = task_type['type_name']

        assert self.default_task_type, 'None default task type in config file'

        for video_config in configs:
            self.task_counter[video_config['id']] = {'task_type': self.default_task_type, 'counter': 0}
        return {'msg': 'register new config successfully'}

    async def get_task_type(self, request: Request):
        data = await request.json()
        source_id = data['id']
        task_type = self.task_counter[source_id]['task_type']
        pipeline = self.configs[task_type]['pipeline']

        self.task_counter[source_id]['counter'] -= 1
        if self.task_counter[source_id]['counter'] == 0:
            self.task_counter[source_id]['task_type'] = self.default_task_type

        return {'task_type': task_type, 'pipeline': pipeline}

    async def query_new_task(self, request: Request):
        data = await request.json()
        task_type = data['task_type']
        cycle_num = data['cycle_num']

        if task_type not in self.configs:
            return {'msg': 'Invalid task type.', 'success': False}
        if task_type != self.default_task_type and (task_type != type(cycle_num) != int or cycle_num <= 0):
            return {'msg': 'Invalid cycle number.', 'success': False}

        for source_id in self.task_counter:
            counter = self.task_counter[source_id]
            counter['task_type'] = task_type
            if task_type == self.default_task_type:
                counter['counter'] = 0
            else:
                counter['counter'] = cycle_num
        return {'msg': 'Task submit success.', 'success': True}


app = ScheduleServer().app
