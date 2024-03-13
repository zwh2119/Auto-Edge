import json
import os

from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form

from fastapi.routing import APIRoute
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from utils import *
from log import LOGGER
from client import http_request
from config import Context


class ControllerServer:
    def __init__(self):
        self.app = FastAPI(routes=[
            APIRoute('/submit_task',
                     self.deal_response,
                     response_class=JSONResponse,
                     methods=['POST']
                     ),
        ], log_level='trace', timeout=6000)

        node_info = get_nodes_info()

        self.service_ports_dict = json.loads(Context.get_parameters('service_port'))
        self.distributor_port = Context.get_parameters('distributor_port')
        self.distributor_ip = node_info[Context.get_parameters('distributor_name')]
        self.distribute_address = get_merge_address(self.distributor_ip, port=self.distributor_port, path='distribute')

        self.local_ip = node_info[Context.get_parameters('NODE_NAME')]

        self.scheduler_ip = node_info[Context.get_parameters('scheduler_name')]
        self.scheduler_port = Context.get_parameters('scheduler_port')
        self.scheduler_address = get_merge_address(self.scheduler_ip, port=self.scheduler_port, path='priority')

        self.app.add_middleware(
            CORSMiddleware, allow_origins=["*"], allow_credentials=True,
            allow_methods=["*"], allow_headers=["*"],
        )

    def service_transmit(self, data, file_data):

        data = json.loads(data)

        # get json data
        source_id = data['source_id']
        task_id = data['task_id']
        pipeline = data['pipeline_flow']
        priority = data['priority']
        tmp_data = data['tmp_data']
        index = data['cur_flow_index']
        scenario = data['scenario_data']
        content = data['content_data']

        # LOGGER.debug(f'controller get data from source {source_id}')

        # get file data(video)
        tmp_path = f'tmp_receive_source_{source_id}_task_{task_id}.mp4'
        with open(tmp_path, 'wb') as buffer:
            buffer.write(file_data)

        # end record transmit time
        tmp_data, transmit_time = record_time(tmp_data, f'transmit_time_{index}', read_only=True)
        if transmit_time != -1:
            pipeline[index]['execute_data']['transmit_time'] = transmit_time

        # execute pipeline
        if index < len(pipeline) - 1:
            cur_service = pipeline[index]

            # transfer to another controller
            task_des_ip = extract_ip_from_address(cur_service['execute_address'])
            assert task_des_ip
            if task_des_ip != self.local_ip:
                LOGGER.debug(f'task_des_ip:{task_des_ip} local_ip:{self.local_ip}  transmit!')
                tmp_data, transmit_time = record_time(tmp_data, f'transmit_time_{index}')
                assert transmit_time == -1

                data['pipeline_flow'] = pipeline
                data['tmp_data'] = tmp_data
                data['cur_flow_index'] = index
                data['content_data'] = content
                data['scenario_data'] = scenario

                # post to other controllers
                http_request(url=cur_service['execute_address'], method='POST',
                             data={'data': json.dumps(data)},
                             files={'file': (data['file_name'],
                                             open(tmp_path, 'rb'),
                                             'video/mp4')}
                             )

                LOGGER.debug(f'controller post data from source {source_id} to other controller')
            else:

                pipeline[index]['execute_data']['transmit_time'] = 0


                LOGGER.debug(f'before priority request: {data["priority"]}')
                response = http_request(url=self.scheduler_address, json=data)
                priority[index] = response['priority']

                data['pipeline_flow'] = pipeline
                data['tmp_data'] = tmp_data
                data['cur_flow_index'] = index
                data['content_data'] = content
                data['scenario_data'] = scenario
                data['priority'] = priority

                LOGGER.debug(f'after priority request: {data["priority"]}')

                # post to service
                service_name = pipeline[index]['service_name']
                assert service_name in self.service_ports_dict, f'service {service_name} not in service dict!'
                service_address = get_merge_address(self.local_ip, port=self.service_ports_dict[service_name],
                                                    path='predict')
                LOGGER.debug(f'post data to service {service_name}')
                LOGGER.debug(f'tmp_path file exist: {os.path.exists(tmp_path)}')

                # start record service time
                tmp_data, service_time = record_time(tmp_data, f'service_time_{index}')
                assert service_time == -1

                LOGGER.debug(f'source {source_id} task {task_id} send to service in time {time.time()}')

                http_request(url=service_address, method='POST',
                             data={'data': json.dumps(data)},
                             files={'file': (data['file_name'], open(tmp_path, 'rb'), 'multipart/form-data')}
                             )

        else:

            # start record transmit time
            tmp_data, transmit_time = record_time(tmp_data, f'transmit_time_{index}')
            assert transmit_time == -1

            data['pipeline_flow'] = pipeline
            data['tmp_data'] = tmp_data
            data['cur_flow_index'] = index
            data['content_data'] = content
            data['scenario_data'] = scenario
            data['priority'] = priority

            # post to distributor
            http_request(url=self.distribute_address, method='POST',
                         data={'data': json.dumps(data)},
                         files={'file': (data['file_name'], open(tmp_path, 'rb'), 'multipart/form-data')}
                         )
            LOGGER.debug(f'controller post data from source {source_id} to distributor')

        os.remove(tmp_path)

    async def deal_response(self, backtask: BackgroundTasks, file: UploadFile = File(...), data: str = Form(...)):
        file_data = await file.read()
        backtask.add_task(self.service_transmit, data, file_data)
        return {'msg': 'data send success!'}


app = ControllerServer().app
