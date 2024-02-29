import datetime
import threading

import eventlet

eventlet.monkey_patch()

import json
import os
import time

import uvicorn
from fastapi import FastAPI, Body, Request

from fastapi.middleware.cors import CORSMiddleware
import requests

from kube_helper import KubeHelper
import yaml
import logging


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
        # print(f'Get invalid status code {response.status_code} in request {url}')
    except Exception as e:
        pass


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
                'prompt': '车流数量',
                'stage': [
                    {
                        "stage_name": "car-detection",
                        "image_list": [
                            {'image_name': 'onecheck/car-detection:v1.0',
                             'url': 'https://hub.docker.com/layers/onecheck/car-detection/v1.0.0'},
                            {'image_name': 'onecheck/car-detection:v1.2',
                             'url': 'https://hub.docker.com/layers/onecheck/car-detection/v1.2.0'},
                            {'image_name': 'onecheck/car-detection:v2.3',
                             'url': 'https://hub.docker.com/layers/onecheck/car-detection/v2.3.0'},
                        ]
                    },
                ]
            },
            {
                'name': 'audio',
                'display': '音频识别',
                'yaml': 'audio.yaml',
                'word': 'audio',
                'prompt': '音频类别',
                'stage': [
                    {
                        "stage_name": "audio-sampling",
                        "image_list": [
                            {'image_name': 'onecheck/audio-sampling:v1.1',
                             'url': 'https://hub.docker.com/layers/onecheck/audio-sampling/v1.1.0'},
                            {'image_name': 'onecheck/audio-sampling:v1.5',
                             'url': 'https://hub.docker.com/layers/onecheck/audio-sampling/v1.5.0'},
                            {'image_name': 'onecheck/audio-sampling:v2.0',
                             'url': 'https://hub.docker.com/layers/onecheck/audio-sampling/v2.0.0'},
                        ]
                    },
                    {
                        "stage_name": "audio-classification",
                        "image_list": [
                            {'image_name': 'onecheck/audio-classification:v1.0',
                             'url': 'https://hub.docker.com/layers/onecheck/audio-classification/v1.0.0'},
                            {'image_name': 'onecheck/audio-classification:v1.4',
                             'url': 'https://hub.docker.com/layers/onecheck/audio-classification/v1.4.0'},
                            {'image_name': 'onecheck/audio-classification:v2.7',
                             'url': 'https://hub.docker.com/layers/onecheck/audio-classification/v2.7.0'},
                        ]
                    },
                ]
            },
            {
                'name': 'imu',
                'display': '惯性轨迹感知',
                'yaml': 'imu.yaml',
                'word': 'imu',
                'prompt': 'IMU轨迹长度',
                'stage': [
                    {
                        "stage_name": "imu-trajectory-sensing",
                        "image_list": [
                            {'image_name': 'onecheck/imu-trajectory-sensing:v1.1',
                             'url': 'https://hub.docker.com/layers/onecheck/imu-trajectory-sensing/v1.1.0'},
                            {'image_name': 'onecheck/imu-trajectory-sensing:v1.5',
                             'url': 'https://hub.docker.com/layers/onecheck/imu-trajectory-sensing/v1.5.0'},
                            {'image_name': 'onecheck/imu-trajectory-sensing:v2.2',
                             'url': 'https://hub.docker.com/layers/onecheck/imu-trajectory-sensing/v2.2.0'},
                        ]
                    },
                ]
            },
            {
                'name': 'edge-eye',
                'display': '工业视觉纠偏',
                'yaml': 'edge-eye.yaml',
                'word': 'eye',
                'prompt': '材料中心点位置',
                'stage': [
                    {
                        "stage_name": "edge-eye-stage1",
                        "image_list": [
                            {'image_name': 'onecheck/edge-eye-stage1:v1.0',
                             'url': 'https://hub.docker.com/layers/onecheck/edge-eye-stage1/v1.0.0'},
                            {'image_name': 'onecheck/edge-eye-stage1:v1.6',
                             'url': 'https://hub.docker.com/layers/onecheck/edge-eye-stage1/v1.6.0'},
                            {'image_name': 'onecheck/edge-eye-stage1:v2.3',
                             'url': 'https://hub.docker.com/layers/onecheck/edge-eye-stage1/v2.3.0'},
                        ]
                    },
                    {
                        "stage_name": "edge-eye-stage2",
                        "image_list": [
                            {'image_name': 'onecheck/edge-eye-stage2:v1.2',
                             'url': 'https://hub.docker.com/layers/onecheck/edge-eye-stage2/v1.2.0'},
                            {'image_name': 'onecheck/edge-eye-stage2:v1.5',
                             'url': 'https://hub.docker.com/layers/onecheck/edge-eye-stage2/v1.5.0'},
                            {'image_name': 'onecheck/edge-eye-stage2:v2.3',
                             'url': 'https://hub.docker.com/layers/onecheck/edge-eye-stage2/v2.3.0'},
                        ]
                    },
                    {
                        "stage_name": "edge-eye-stage3",
                        "image_list": [
                            {'image_name': 'onecheck/edge-eye-stage3:v1.4',
                             'url': 'https://hub.docker.com/layers/onecheck/edge-eye-stage3/v1.4.0'},
                            {'image_name': 'onecheck/edge-eye-stage3:v1.7',
                             'url': 'https://hub.docker.com/layers/onecheck/edge-eye-stage3/v1.7.0'},
                            {'image_name': 'onecheck/edge-eye-stage3:v2.0',
                             'url': 'https://hub.docker.com/layers/onecheck/edge-eye-stage3/v2.0.0'},
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
                        "name": "交通摄像头1",
                        "url": "rtsp://192.168.1.51/video0",
                        "describe": "高速公路监控摄像头",
                        "resolution": "1080p",
                        "fps": "25fps"

                    },
                    {
                        "name": "交通摄像头2",
                        "url": "rtsp://192.168.1.55/video1",
                        "describe": "十字路口监控摄像头",
                        "resolution": "1080p",
                        "fps": "30fps"
                    }
                ]

            },
            {
                "source_label": "audio",
                "source_name": "音频数据流",
                "source_type": "音频流",
                "camera_list": [
                    {
                        "name": "音频流1",
                        "url": "http://192.168.2.22:3381/audio",
                        "describe": "音频来源1",

                    },
                    {
                        "name": "音频流2",
                        "url": "http://192.168.2.22:3382/audio",
                        "describe": "音频来源2",
                    }
                ]

            },
            {
                "source_label": "imu",
                "source_name": "惯性数据流",
                "source_type": "IMU流",
                "camera_list": [
                    {
                        "name": "IMU流1",
                        "url": "http://192.168.2.11:3000/imu",
                        "describe": "IMU场景1",

                    },
                    {
                        "name": "IMU流2",
                        "url": "http://192.168.2.91:3001/imu",
                        "describe": "IMU场景2",
                    }
                ]

            },
            {
                "source_label": "edge-eye",
                "source_name": "工厂摄像头",
                "source_type": "视频流",
                "camera_list": [
                    {
                        "name": "工厂摄像头1",
                        "url": "rtsp://192.168.1.67/video0",
                        "describe": "工厂1",
                        "resolution": "1080p",
                        "fps": "25fps"

                    },
                    {
                        "name": "工厂摄像头2",
                        "url": "rtsp://192.168.1.83/video1",
                        "describe": "工厂2",
                        "resolution": "1080p",
                        "fps": "25fps"
                    }
                ]

            },

        ]

        self.devices = {
            'http://114.212.81.11:39200/submit_task': 'cloud',
            'http://192.168.1.2:39200/submit_task': 'edge1',
            'http://192.168.1.4:39200/submit_task': 'edge2',
        }

        self.time_ticket = 0

        self.templates_path = '/home/hx/zwh/Auto-Edge/templates'
        self.free_task_url = 'http://114.212.81.11:39400/task'

        self.result_url = 'http://114.212.81.11:39500/result'

        self.resource_url = 'http://114.212.81.11:39400/resource'
        self.parameters_url = 'http://114.212.81.11:39400/parameters'

        self.source_open = False

        self.source_label = ''

        self.save_logs_path = ''

        self.task_results = []
        self.queue_results = []

        self.free_open = {}
        self.is_free_result = {}
        self.free_start = {}
        self.free_end = {}
        self.free_duration = {}

    def get_result(self):
        time_ticket = 0
        while True:
            response = http_request(self.result_url, method='GET', json={'time_ticket': time_ticket, 'size': 0})
            if response:
                time_ticket = response["time_ticket"]
            time.sleep(1)

    def timer(self, duration, source_label):
        self.free_start[source_label] = f'{datetime.datetime.now():%T}'
        time.sleep(duration)
        self.free_end[source_label] = f'{datetime.datetime.now():%T}'
        if source_label in self.free_open:
            self.is_free_result[source_label] = True

    def clear_free(self, source_label):
        if source_label in self.free_open:
            del self.free_open[source_label]
        if source_label in self.is_free_result:
            del self.is_free_result[source_label]
        if source_label in self.free_start:
            del self.free_start[source_label]
        if source_label in self.free_end:
            del self.free_end[source_label]
        if source_label in self.free_duration:
            del self.free_duration[source_label]


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
    data = json.loads(str(data, encoding='utf-8'))

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
    print(f'yaml_file: {yaml_file}')

    try:
        with eventlet.Timeout(40, True):
            result = KubeHelper.apply_custom_resources(yaml_file)
            while not KubeHelper.check_pods_running('auto-edge'):
                time.sleep(1)

    except eventlet.timeout.Timeout as e:
        logging.exception(e)
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
    try:
        info = KubeHelper.get_service_info(service_name=service)
        resource_data = http_request(server.resource_url, method='GET')
        # print(resource_data)
        for single_info in info:
            single_info['bandwidth'] = f"{resource_data[single_info['hostname']]['bandwidth']:.2f}Mbps" if \
                resource_data[single_info['hostname']]['bandwidth'] != 0 else '-'
    except Exception as e:
        logging.exception(e)
        return []

    return info


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
def submit_query(data=Body(...)):
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

    data = json.loads(str(data, encoding='utf-8'))

    source_label = data['source_label']
    delay_constraint = data['delay_cons']
    acc_constraint = data['acc_cons']
    urgency_weight = data['urgency']
    importance_weight = data['importance']

    http_request(server.parameters_url, method='POST', json={'user_constraint': delay_constraint,
                                                             'urgency_weight': urgency_weight,
                                                             'importance_weight': importance_weight})

    server.source_open = True
    server.source_label = source_label

    return {'state': 'success', 'msg': '数据流打开成功'}


@app.post('/stop_service')
async def stop_service():
    """
    {'state':"success/fail",'msg':'...'}

    :return:
    """

    try:
        with eventlet.Timeout(120, True):
            result = KubeHelper.delete_resources('auto-edge')
            while KubeHelper.check_pods_exist('auto-edge'):
                time.sleep(1)

    except eventlet.timeout.Timeout as e:
        logging.exception(e)
        result = False

    if result:
        return {'state': 'success', 'msg': '服务停止成功'}
    else:
        return {'state': 'fail', 'msg': '服务停止失败，请联系管理员'}


@app.post('/stop_query')
async def stop_query():
    """
    {'source_label':'...'}
    :return:
    {'state':"success/fail",'msg':'...'}
    """

    server.source_open = False
    server.source_label = ''

    return {'state': 'success', 'msg': '数据流关闭成功'}


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
    return {'state': 'open' if server.source_open else 'close', 'source_label': server.source_label}


@app.get('/source_list')
async def get_source_list():
    """
    [
        {
            "id":"video_source1",
            "label":"数据源1"
        },
        ...
    ]
    :return:
    """
    if server.source_open:
        for source in server.sources:
            if source['source_label'] == server.source_label:
                return [camera['name'] for camera in source['camera_list']]
    else:
        return []


@app.get('/pipeline_info')
async def get_pipeline_info():
    """[stage_name1,stage_name2]"""

    if KubeHelper.check_pods_running('auto-edge'):
        for task in server.tasks:
            if KubeHelper.check_pod_name(task['word']):
                return [stage['stage_name'] for stage in task['stage']]
    else:
        return []


@app.get('/result_prompt')
async def get_result_prompt():
    """
    结果提示文字
    :return:
    {'prompt':'...'}
    """
    if KubeHelper.check_pods_running('auto-edge'):
        for task in server.tasks:
            if KubeHelper.check_pod_name(task['word']):
                return {'prompt': task['prompt']}
    else:
        return {'prompt': ''}


@app.get('/task_result')
async def get_task_result():
    """
    10个最近
    {
    'datasource1':[
        taskId: 12,
        result: 23 (数值),
        delay: 0.6,
        visualize: "" (base64编码image)

    ],
    'datasource2':[]
    }
    :return:
    """
    pass


@app.get('/queue_result')
async def get_queue_result():
    """
    10个
    {
        'datasource1':
        [
            {
                taskId: 1,
                priorityTrace:[
                    {urgency:x
                    importance:x
                    priority:x},
                    {}
                ]
            },
            {...}
        ],

    }
    :return:
    """
    pass


@app.post('/start_free_task')
async def start_free_task(data=Body(...)):
    """
    body
        {
            'source_label':'...',
            'duration':20  (seconds)
        }


    :return:
    """
    source_label = data['source_label']
    duration = data['duration']
    if source_label in server.free_open:
        return {'state': 'fail', 'msg': '启动自由任务失败，该数据源有自由任务正在执行'}
    server.free_open[source_label] = True
    server.is_free_result[source_label] = False
    server.free_duration[source_label] = duration
    threading.Thread(target=server.timer).start()

    return {'state': 'success', 'msg': '启动自由任务成功'}


@app.get('/free_state/{source}')
async def get_free_state(source):
    """

    :return:
    {
        'state':0/1,
        'duration':20
    }
    """
    if source not in server.free_open:
        return {'state': 0}
    else:
        return {'state': 1, 'duration': server.free_duration[source]} if server.free_open[source] else {'state': 0}


@app.get('/stop_free_task/{source}')
async def stop_free_task(source):
    """
    终止自由任务
    :param source:
    :return:
    """
    if source in server.free_open:
        server.clear_free(source)

        return {'state': 'success', 'msg': '终止自由任务成功'}
    else:
        return {'state': 'fail', 'msg': '终止自由任务失败，该数据源未开启自由任务'}


@app.get('/free_task_result/{source}')
async def get_free_task_result(source):
    """

    :param source:
    :return:
    {
        'state':0/1,(是否有结果)
        'task_info':
        [
            {name:任务数量, value:20},
            {name:最大, value:20},
            {name:平均, value:20},
        ],

        'delay':[
            时延数据
        ],
        'start_time': 'xxx',
        'end_time': 'xxx'

    }
    """

    pass


def main():
    threading.Thread(target=server.get_result).start()
    uvicorn.run(app, host='0.0.0.0', port=8910)


if __name__ == '__main__':
    main()
