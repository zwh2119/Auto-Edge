import copy
import json
import os
import shutil

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

        self.local_ip = node_info[Context.get_parameters('NODE_NAME')]

        self.distribute_address = get_merge_address(self.distributor_ip, port=self.distributor_port, path='distribute')

        self.app.add_middleware(
            CORSMiddleware, allow_origins=["*"], allow_credentials=True,
            allow_methods=["*"], allow_headers=["*"],
        )

    def service_transmit(self, data, file):

        data = json.loads(data)

        # get json data
        source_id = data['source_id']
        task_id = data['task_id']
        pipeline = data['pipeline_flow']
        tmp_data = data['tmp_data']
        index = data['cur_flow_index']
        scenario = data['scenario_data']
        content = data['content_data']

        LOGGER.debug(f'controller get data from source {source_id}')

        # get file data(video)
        tmp_path = f'tmp_receive_source_{source_id}_task_{task_id}.mp4'
        with open(tmp_path, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)
            del file

        # end record transmit time
        tmp_data, transmit_time = record_time(tmp_data, f'transmit_time_{index}')
        assert transmit_time != -1
        pipeline[index]['execute_data']['transmit_time'] = transmit_time

        # execute pipeline
        while index < len(pipeline) - 1:
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
                             files={'file': (f'tmp_{source_id}.mp4',
                                             open(tmp_path, 'rb'),
                                             'video/mp4')}
                             )

                LOGGER.debug(f'controller post data from source {source_id} to other controller')
                os.remove(tmp_path)
                return
            else:
                pipeline[index]['execute_data']['transmit_time'] = 0

            # start record service time
            tmp_data, service_time = record_time(tmp_data, f'service_time_{index}')
            assert service_time == -1

            # post to service
            service_name = pipeline[index]['service_name']
            assert service_name in self.service_ports_dict
            service_address = get_merge_address(self.local_ip, port=self.service_ports_dict[service_name],
                                                path='predict')
            service_return = http_request(url=service_address, method='POST',
                                          data={'data': json.dumps(content)},
                                          files={'file': (f'tmp_{source_id}.mp4', open(tmp_path, 'rb'), 'video/mp4')}
                                          )

            if service_return is None:
                content = 'discard'
                break

            # end record service time
            tmp_data, service_time = record_time(tmp_data, f'service_time_{index}')
            assert service_time != -1
            pipeline[index]['execute_data']['service_time'] = service_time
            LOGGER.debug(f'service_time of {source_id}:{service_time}s')

            # deal with service result
            if 'parameters' in service_return:
                scenario.update(service_return['parameters'])
            content = copy.deepcopy(service_return['result'])

            index += 1

        # start record transmit time
        tmp_data, transmit_time = record_time(tmp_data, f'transmit_time_{index}')
        assert transmit_time == -1

        data['pipeline_flow'] = pipeline
        data['tmp_data'] = tmp_data
        data['cur_flow_index'] = index
        data['content_data'] = content
        data['scenario_data'] = scenario

        # post to distributor
        http_request(url=self.distribute_address, method='POST', json=data)
        LOGGER.debug(f'controller post data from source {source_id} to distributor')

        os.remove(tmp_path)

    async def deal_response(self, backtask: BackgroundTasks, file: UploadFile = File(...), data: str = Form(...)):
        backtask.add_task(self.service_transmit, data, file)
        return {'msg': 'data send success!'}


app = ControllerServer().app
