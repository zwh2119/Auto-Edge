import os
import time

import uvicorn
from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form, Body, Request

from fastapi.routing import APIRoute
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from kubernetes import client, config
import requests

from kubernetes import client, config
config.kube_config.load_kube_config(config_file="/root/kubeconfig.yaml")


class BackendServer:
    def __init__(self):
        self.tasks = [
            {
                'name': 'road-detection',
                'display': '交通路面监控',
                'yaml': 'video_car_detection.yaml',
                'stage': [

                ]
            },
            {
                'name': 'audio',
                'display': '音频识别',
                'yaml': 'audio.yaml',
                'stage': [

                ]
            },
            {
                'name': 'imu',
                'display': '惯性轨迹感知',
                'yaml': 'imu.yaml',
                'stage': [

                ]
            },
            {
                'name': 'edge-eye',
                'display': '工业视觉纠偏',
                'yaml': 'edge-eye.yaml',
                'stage': [

                ]
            },
        ]

        self.sources = [
            {
                "source_label": "car",
                "source_name": "交通监控摄像头",
                "source_type": "视频流",
                "camera_list": [
                    {
                        "name": "摄像头1",
                        "url": "rtsp/114.212.81.11...",
                        "describe": "某十字路口",
                        "resolution": "1080p",
                        "fps": "25fps"

                    },
                    {}
                ]

            }
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

    def install_service(self):
        pass

    def open_data_source(self):
        pass

    def uninstall_service(self):
        pass

    def close_data_source(self):
        pass

    def get_install_state(self):
        pass

    def get_data_source_state(self):
        pass

    def get_installed_service_info(self):
        pass


server = BackendServer()

app = FastAPI()

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)


@app.get('/task')
async def get_all_task():
    """

    :return:
    """
    tasks = []
    for task in server.tasks:
        tasks.append({task['name']: task['display']})
    return tasks


@app.get('/get_task_stage/{task}')
async def get_service_stage(task):
    """

    :param task:
    :return:
    [
        {
            'stage_name':'face_detection',
            'image_list':[
            {'image_name':'onecheck/face_detection:v1',"url":"..."},
            ]
        },
    ]
    """
    for server_task in server.tasks:
        if server_task['name'] == task:
            return server_task['stage']

    assert None, f'task name {task} error!'


@app.post('/install')
async def install_service():
    """
    body
    {
        "task_name": "face",
        "image_list": ["", ""]
    }
    :return:
    {'msg': 'service start successfully'}
    {'msg': 'Invalid service name!'}
    """
    pass


@app.get("/get_service_list")
async def get_service_list():
    """
    已下装服务容器
    :return:
    ["face_detection", "..."]
    """
    pass


@app.get("/get_execute_url/{service}")
async def get_service_info(service):
    """
    返回已安装服务容器的具体情况
    :param service:
    :return:
    [
        {
            "ip":114.212.81.11
            "hostname"
            “cpu”:
            "memory":
            "bandwidth"
            "age"
        }
    ]
    {
                "114.212.81.11:5500": {
                    "bandwidth": 1,
                    "cpu": 1,
                    "mem": 1,
                    "url": "http://114.212.81.11:5500/execute_task/face_detection"
                },
                "172.27.138.183:5501": {
                    "bandwidth": 1,
                    "cpu": 1,
                    "mem": 1,
                    "url": "http://172.27.138.183:5501/execute_task/face_detection"
                },
                "172.27.151.135:5501": {
                    "bandwidth": 1,
                    "cpu": 1,
                    "mem": 1,
                    "url": "http://172.27.151.135:5501/execute_task/face_detection"
                }
            }

    """
    pass


@app.get("/node/get_video_info")
async def get_video_info():
    """
    :return:

        [
        {
            "source_label": "car"
            "source_name": "交通监控摄像头",
            “source_type”: "视频流",
            "camera_list":[
                {
                    "name": "摄像头1",
                    "url": "rtsp/114.212.81.11...",
                    "describe":"某十字路口"
                    “resolution”: "1080p"
                    "fps":"25fps"

                },
                {}
            ]


        }

    ]
    """
    return server.sources


@app.post("/query/submit_query")
def submit_task():
    """
    body
    {
        "source_label": "..."
        "delay_cons":"0.6",
        "acc_cons":"0.6",
        "urgency": "0.1",
        "importance":"0.9"
    }
    :return:
    {'msg': 'service start successfully'}
    {'msg': 'Invalid service name!'}
    """
    pass


@app.post('/stop_service')
async def stop_service():
    """
    {'state':"success/fail",'msg':'...'}

    :return:
    """
    pass


@app.post('/stop_query')
async def stop_query():
    """
    {'source_label':'...'}
    :return:
    {'state':"success/fail",'msg':'...'}
    """
    pass


@app.get('/install_state')
async def get_install_state():
    """
    :return:
    {'state':'install/uninstall'}
    """
    pass


@app.get('/query_state')
async def get_query_state():
    """

    :return:
    {'state':'open/close','source_label':''}
    """
    pass


def main():
    uvicorn.run(app, host='0.0.0.0', port=8910)


if __name__ == '__main__':
    main()
