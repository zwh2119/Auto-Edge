import os
import time

import uvicorn
from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form, Body, Request

from fastapi.routing import APIRoute
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from kubernetes import client, config
import requests


def http_request(url,
                 method=None,
                 timeout=None,
                 binary=True,
                 no_decode=False,
                 **kwargs):
    _maxTimeout = timeout if timeout else 300
    _method = 'GET' if not method else method

    try:
        response = requests.request(method=_method, url=url, **kwargs)
        if response.status_code == 200:
            if no_decode:
                return response
            else:
                return response.json() if binary else response.content.decode('utf-8')
        elif 200 < response.status_code < 400:
            print(f'Redirect URL: {response.url}')
        print(f'Get invalid status code {response.status_code} in request {url}')
    except (ConnectionRefusedError, requests.exceptions.ConnectionError):
        print(f'Connection refused in request {url}')
    except requests.exceptions.HTTPError as err:
        print(f'Http Error in request {url}: {err}')
    except requests.exceptions.Timeout as err:
        print(f'Timeout error in request {url}: {err}')
    except requests.exceptions.RequestException as err:
        print(f'Error occurred in request {url}: {err}')


class BackendServer:
    def __init__(self):
        self.app = FastAPI(routes=[
            APIRoute('/info',
                     self.get_system_info,
                     response_class=JSONResponse,
                     methods=['GET']
                     ),
            APIRoute('/task',
                     self.get_all_task,
                     response_class=JSONResponse,
                     methods=['GET']
                     ),
            APIRoute('/start',
                     self.start_task,
                     response_class=JSONResponse,
                     methods=['POST']
                     ),
            APIRoute('/result',
                     self.get_execute_result,
                     response_class=JSONResponse,
                     methods=['POST']
                     ),
            APIRoute('/free',
                     self.start_free_task,
                     response_class=JSONResponse,
                     methods=['POST']
                     ),
            APIRoute('/time_ticket',
                     self.get_time_ticket,
                     response_class=JSONResponse,
                     methods=['GET']
                     ),
            APIRoute('/device',
                     self.get_devices,
                     response_class=JSONResponse,
                     methods=['GET'])
        ], log_level='trace', timeout=6000)

        self.app.add_middleware(
            CORSMiddleware, allow_origins=["*"], allow_credentials=True,
            allow_methods=["*"], allow_headers=["*"],
        )

        self.tasks = [
            {'name': 'road-detection', 'display': '交通路面监控', 'yaml': 'video_car_detection.yaml'},
            {'name': 'audio', 'display': '音频识别', 'yaml': 'audio.yaml'},
            {'name': 'imu', 'display': '惯性轨迹感知', 'yaml': 'imu.yaml'},
            {'name': 'edge-eye', 'display': '工业视觉纠偏', 'yaml': 'edge-eye.yaml'},
        ]
        self.tasks_dict = {'car': '路面交通监控', 'human': '路面行人监控',
                           'audio': '音频识别', 'imu': '惯性轨迹感知',
                           'edge-eye': '工业视觉纠偏'}

        self.devices = {
            'http://114.212.81.11:39200/submit_task': 'cloud',
            'http://192.168.1.2:39200/submit_task': 'edge1',
            'http://192.168.1.4:39200/submit_task': 'edge2',
        }

        self.time_ticket = 0

        self.templates_path = '/home/hx/zwh/Auto-Edge/templates'
        self.free_task_url = 'http://114.212.81.11:39400/task'
        self.result_url = 'http://114.212.81.11:39500/result'

    def get_system_info(self):
        config.load_kube_config()
        v1 = client.CoreV1Api()
        nodes = v1.list_node().items

        node_dict = {}

        for node in nodes:
            node_name = node.metadata.name
            addresses = node.status.addresses
            for address in addresses:
                if address.type == "InternalIP":
                    node_dict[node_name] = address.address

        return node_dict

    def get_all_task(self):
        tasks = []
        for task in self.tasks:
            tasks.append({task['name']: task['display']})
        return tasks

    def start_task(self, data=Body(...)):
        service_name = data['service_name']
        yaml_name = None
        print(service_name)
        for task in self.tasks:
            if task['name'] == service_name:
                yaml_name = task['yaml']
        if yaml_name is None:
            return {'msg': 'Invalid service name!'}
        yaml_path = os.path.join(self.templates_path, yaml_name)
        print(f'apply yaml: {yaml_path}')
        os.system(f'kubectl apply -f {yaml_path}')
        time.sleep(15)
        return {'msg': 'service start successfully'}

    async def get_execute_result(self, data: Request):
        input_json = await data.json()
        print(input_json)
        time_ticket = input_json['time_ticket']
        size = input_json['size']

        response = http_request(url=self.result_url, method='GET', json={'time_ticket': time_ticket, "size": size})
        if response:
            for task in response['result']:
                task['task_type'] = self.tasks_dict[task['task_type']]
            self.time_ticket = response['time_ticket']
            print(response)
            return response
        else:
            return {}

    def get_time_ticket(self):
        print(f'time_ticket: {self.time_ticket}')
        return {'time_ticket': self.time_ticket}

    def start_free_task(self, data=Body(...)):
        service_name = data['service_name']
        duration = data['time']
        response = http_request(self.free_task_url, method='POST',
                                json={'task_type': service_name, 'cycle_num': duration})
        return {'msg': 'free service start successfully'}

    def get_devices(self):
        return self.devices

    def start_uvicorn_server(self):
        uvicorn.run(self.app, host='0.0.0.0', port=8910)


if __name__ == '__main__':
    server = BackendServer()
    server.start_uvicorn_server()
