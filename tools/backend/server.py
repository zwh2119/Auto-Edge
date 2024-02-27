import os
import time

import uvicorn
from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form, Body, Request

from fastapi.routing import APIRoute
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import eventlet
from kube_helper import KubeHelper
import yaml


def read_yaml(yaml_file):
    '''读取yaml文件'''
    with open(yaml_file, 'r', encoding="utf-8") as f:
        values = yaml.load(f, Loader=yaml.Loader)
    return values


def write_yaml(value_dict, yaml_file):
    '''写yaml文件'''
    with open(yaml_file, 'a', encoding="utf-8") as f:
        try:
            yaml.dump(data=value_dict, stream=f, encoding="utf-8", allow_unicode=True)
        except Exception as e:
            print(e)


class BackendServer:
    def __init__(self):
        self.tasks = [
            {
                'name': 'road-detection',
                'display': '交通路面监控',
                'yaml': 'video_car_detection.yaml',
                'word': 'car',
                'stage': [
                    {
                        "stage_name": "car-detection",
                        "image_list": [
                            {'image_name': 'onecheck/car-detection:v1.0', 'url': '...'},
                            {'image_name': 'onecheck/car-detection:v1.5', 'url': '...'},
                            {'image_name': 'onecheck/car-detection:v2.0', 'url': '...'},
                        ]
                    },
                ]
            },
            {
                'name': 'audio',
                'display': '音频识别',
                'yaml': 'audio.yaml',
                'word': 'audio',
                'stage': [
                    {
                        "stage_name": "audio-sampling",
                        "image_list": [
                            {'image_name': 'onecheck/audio-sampling:v1.0', 'url': '...'},
                            {'image_name': 'onecheck/audio-sampling:v1.5', 'url': '...'},
                            {'image_name': 'onecheck/audio-sampling:v2.0', 'url': '...'},
                        ]
                    },
                    {
                        "stage_name": "audio-classification",
                        "image_list": [
                            {'image_name': 'onecheck/audio-classification:v1.0', 'url': '...'},
                            {'image_name': 'onecheck/audio-classification:v1.5', 'url': '...'},
                            {'image_name': 'onecheck/audio-classification:v2.0', 'url': '...'},
                        ]
                    },
                ]
            },
            {
                'name': 'imu',
                'display': '惯性轨迹感知',
                'yaml': 'imu.yaml',
                'word': 'imu',
                'stage': [
                    {
                        "stage_name": "imu-trajectory-sensing",
                        "image_list": [
                            {'image_name': 'onecheck/imu-trajectory-sensing:v1.0', 'url': '...'},
                            {'image_name': 'onecheck/imu-trajectory-sensing:v1.5', 'url': '...'},
                            {'image_name': 'onecheck/imu-trajectory-sensing:v2.0', 'url': '...'},
                        ]
                    },
                ]
            },
            {
                'name': 'edge-eye',
                'display': '工业视觉纠偏',
                'yaml': 'edge-eye.yaml',
                'word': 'eye',
                'stage': [
                    {
                        "stage_name": "edge-eye-stage1",
                        "image_list": [
                            {'image_name': 'onecheck/edge-eye-stage1:v1.0', 'url': '...'},
                            {'image_name': 'onecheck/edge-eye-stage1:v1.5', 'url': '...'},
                            {'image_name': 'onecheck/edge-eye-stage1:v2.0', 'url': '...'},
                        ]
                    },
                    {
                        "stage_name": "edge-eye-stage2",
                        "image_list": [
                            {'image_name': 'onecheck/edge-eye-stage2:v1.0', 'url': '...'},
                            {'image_name': 'onecheck/edge-eye-stage2:v1.5', 'url': '...'},
                            {'image_name': 'onecheck/edge-eye-stage2:v2.0', 'url': '...'},
                        ]
                    },
                    {
                        "stage_name": "edge-eye-stage3",
                        "image_list": [
                            {'image_name': 'onecheck/edge-eye-stage3:v1.0', 'url': '...'},
                            {'image_name': 'onecheck/edge-eye-stage3:v1.5', 'url': '...'},
                            {'image_name': 'onecheck/edge-eye-stage3:v2.0', 'url': '...'},
                        ]
                    },
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
                    {
                        "name": "摄像头1",
                        "url": "rtsp/114.212.81.11...",
                        "describe": "某十字路口",
                        "resolution": "1080p",
                        "fps": "25fps"
                    }
                ]

            },
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
                    {
                        "name": "摄像头1",
                        "url": "rtsp/114.212.81.11...",
                        "describe": "某十字路口",
                        "resolution": "1080p",
                        "fps": "25fps"
                    }
                ]

            },
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
                    {
                        "name": "摄像头1",
                        "url": "rtsp/114.212.81.11...",
                        "describe": "某十字路口",
                        "resolution": "1080p",
                        "fps": "25fps"
                    }
                ]

            },
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
                    {
                        "name": "摄像头1",
                        "url": "rtsp/114.212.81.11...",
                        "describe": "某十字路口",
                        "resolution": "1080p",
                        "fps": "25fps"
                    }
                ]

            },

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
async def install_service(data=Body(...)):
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

    task_name = data['task_name']
    images = data['image_list']

    cur_task = None

    for task in server.tasks:
        if task['name'] == task_name:
            cur_task = task
            break

    if cur_task is None:
        return {'state': 'fail', 'msg': '服务不存在'}

    yaml_file = os.path.join(server.templates_path, cur_task['yaml'])

    eventlet.monkey_patch()
    try:
        with eventlet.Timeout(30, True):
            result = KubeHelper.apply_custom_resources(yaml_file)
            while not KubeHelper.check_pods_running('auto-edge'):
                continue

    except eventlet.timeout.Timeout:
        result = False

    if result:
        return {'state': 'success', 'msg': '服务下装成功'}
    else:
        return {'state': 'fail', 'msg': '服务下装失败，请联系管理员'}


@app.get("/get_service_list")
async def get_service_list():
    """
    已下装服务容器
    :return:
    ["face_detection", "..."]
    """
    if KubeHelper.check_pods_running('auto-edge'):
        for task in server.tasks:
            if KubeHelper.check_pod_name(task['word']):
                return [stage['stage_name'] for stage in task['stage']]
    else:
        return []


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
def submit_query(data: Body(...)):
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
    source_label = data['source_label']
    delay_constraint = data['delay_cons']
    acc_constraint = data['acc_cons']
    urgency_weight = data['urgency']
    importance_weight = data['importance']


@app.post('/stop_service')
async def stop_service():
    """
    {'state':"success/fail",'msg':'...'}

    :return:
    """
    eventlet.monkey_patch()
    try:
        with eventlet.Timeout(30, True):
            result = KubeHelper.delete_resources('auto-edge')

    except eventlet.timeout.Timeout:
        result = False

    if result:
        return
    else:
        return


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
    state = 'install' if KubeHelper.check_pods_exist('auto-edge') else 'uninstall'
    return {'state': state}


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
