import base64
import datetime
import threading

import numpy as np

import json
import os
import time

import uvicorn
from fastapi import FastAPI, Body, Request, File, UploadFile
from starlette.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import requests

from kube_helper import KubeHelper
import yaml
import logging
import queue
import cv2

import sys

sys.path.append('/home/hx/zwh/Auto-Edge-rebuild/dependency')

from core.lib.content import Task
from core.lib.common import timeout, LOGGER
from core.lib.network import http_request


class NameCounter:
    counter = 0

    @classmethod
    def get_name_counter(cls):
        cls.counter += 1
        return cls.counter


class ResultQueue:
    def __init__(self, length=0):
        self.__queue = queue.Queue()
        self.__length = length
        self.__lock = threading.Lock()

    def pop(self):
        with self.__lock:
            return self.__queue.get()

    def push(self, obj):
        with self.__lock:
            self.__queue.put(obj)

    def save_results(self, results):
        for result in results:
            self.push(result)
            if 0 < self.__length < self.__queue.qsize():
                self.pop()

    def get_results(self):
        results = []
        while not self.__queue.empty():
            results.append(self.pop())
        return results

    def clear_results(self):
        self.get_results()


class BackendServer:
    def __init__(self):
        self.namespace = 'auto-edge'
        self.tasks = [
            {
                'name': 'road_surveillance',
                'display': '交通路面监控',
                'yaml': 'surveillance_car_detection.yaml',
                'word': 'car',
                'visualizing_prompt': ' - 路面监控画面',
                'result_title_prompt': ' - 实时车流数量',
                'result_text_prompt': '车流数量：实时画面检测结果的平均值',
                'delay_text_prompt': '任务执行时延累计分布曲线 (窗口大小：20)',

                'stage': [
                    {
                        "stage_name": "car-detection",
                        "image_list": [
                            {'image_name': 'onecheck/car-detection:v2.0.0',
                             'url': 'https://hub.docker.com/layers/onecheck/car-detection/v2.0.0'},
                        ]
                    },
                ]
            },

        ]

        self.sources = []

        self.services = [
            {'service_name': 'car-detection',
             'description': '车流检测'},

        ]

        self.pipelines = []

        self.legal_pipelines = {
            'road_surveillance': ['car-detection'],
        }

        self.time_ticket = 0

        self.templates_path = '/home/hx/zwh/Auto-Edge-rebuild/templates/service_yaml'

        self.result_url = 'http://114.212.81.11:39500/result'
        self.result_file_url = 'http://114.212.81.11:39500/file'

        self.resource_url = 'http://114.212.81.11:39400/resource'

        self.source_open = False

        self.source_label = ''

        self.save_logs_path = ''

        self.task_results = {}

        self.is_get_result = False

        self.log_file = 'log.txt'
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
        with open(self.log_file, 'w'):
            pass

    def check_pipeline(self, pipeline):
        for legal_pipeline_name in self.legal_pipelines:
            legal_pipeline = self.legal_pipelines[legal_pipeline_name]
            if legal_pipeline == pipeline:
                return True
        return False

    def get_pipeline_label(self, pipeline):
        for legal_pipeline_name in self.legal_pipelines:
            legal_pipeline = self.legal_pipelines[legal_pipeline_name]
            if legal_pipeline == pipeline:
                return legal_pipeline_name
        return None

    def find_pipeline_by_id(self, dag_id):
        for pipeline in server.pipelines:
            if pipeline['dag_id'] == dag_id:
                return pipeline['dag']
        return None

    def get_source_id(self):
        source_ids = []
        for source in self.sources:
            if source['source_label'] == self.source_label:
                for camera in source['camera_list']:
                    source_ids.append(camera['id'])

        return source_ids

    def run_get_result(self):
        time_ticket = 0
        while self.is_get_result:
            response = http_request(self.result_url, method='GET', json={'time_ticket': time_ticket, 'size': 0})
            if response:
                time_ticket = response["time_ticket"]
                results = response['result']
                for result in results:
                    task = Task.deserialize(result)
                    source_id = task.get_source_id()
                    task_id = task.get_task_id()
                    LOGGER.debug(f'source:{source_id} task:{task_id}')
                    delay = task.calculate_total_time()
                    LOGGER.debug(task.get_delay_info())

                    task_result = result['obj_num']

                    content = task.get_content()
                    file_path = self.get_file_result(source_id, task_id)

                    with open(self.log_file, 'a') as f:
                        log_string = ''
                        log_string += f'log_time:{datetime.datetime.now():%Y-%m-%d %H:%M:%S} '
                        log_string += f'source_id:{source_id} task_id:{task_id} '
                        log_string += f'task_delay: {delay:.4f}s'
                        log_string += '\n'
                        f.write(log_string)

                    if os.path.getsize(self.log_file) > 1024 * 1024 * 10:
                        with open(self.log_file, 'w'):
                            pass

                    base64_data = self.get_base64_data(file_path, content)
                    os.remove(file_path)

                    if not self.source_open:
                        continue

                    source_id_text = self.source_id_num_2_id_text(source_id)
                    self.task_results[source_id_text].save_results([{
                        'taskId': task_id,
                        'result': task_result,
                        'delay': delay,
                        'visualize': base64_data
                    }])

            time.sleep(1)

    @staticmethod
    def check_datasource_config(config):
        try:
            source_label = config['source_label']
            source_name = config['source_name']
            source_type = config['source_type']
            for camera in config['camera_list']:
                camera_id = camera['id']
                camera_name = camera['name']
                camera_url = camera['url']
                camera_describe = camera['describe']

        except Exception as e:
            return False

        return True

    def check_datasource_exists(self, config):
        source_label = config['source_label']
        for source in self.sources:
            if source['source_label'] == source_label:
                return True

        return False

    def get_file_result(self, source_id, task_id):
        file_name = f'file_{source_id}_{task_id}'
        response = http_request(self.result_file_url, method='GET', no_decode=True,
                                json={'source_id': source_id, 'task_id': task_id},
                                stream=True)
        with open(file_name, 'wb') as file_out:
            for chunk in response.iter_content(chunk_size=8192):
                file_out.write(chunk)
        return file_name

    def source_id_num_2_id_text(self, source_id):
        source_id_text_list = self.get_source_id()
        return source_id_text_list[source_id]

    def get_base64_data(self, file,  content):
        video_cap = cv2.VideoCapture(file)
        success, image = video_cap.read()
        image = self.draw_bboxes(image, content[0])

        base64_str = cv2.imencode('.jpg', image)[1].tobytes()
        base64_str = base64.b64encode(base64_str)
        base64_str = bytes('data:image/jpg;base64,', encoding='utf8') + base64_str
        return base64_str

    @staticmethod
    def decode_image(encoded_img_str):
        # 将 Base64 编码的字符串转换回 bytes
        encoded_img_bytes = base64.b64decode(encoded_img_str)
        # 解码图像
        decoded_img = cv2.imdecode(np.frombuffer(encoded_img_bytes, np.uint8), cv2.IMREAD_COLOR)
        return decoded_img

    @staticmethod
    def draw_bboxes(frame, bbox):
        for x_min, y_min, x_max, y_max in bbox:
            cv2.rectangle(frame, (int(x_min), int(y_min)), (int(x_max), int(y_max)), (0, 255, 0), 4)
        return frame

    def get_current_task(self):
        if KubeHelper.check_pods_running(self.namespace):
            for task in server.tasks:
                if KubeHelper.check_pod_name(task['word'], namespace=self.namespace):
                    return task
        else:
            return None


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
    显示已有流水线
    {
        dag_id:id,
        dag_name：name}
    """
    cur_pipelines = []
    for pipeline in server.pipelines:
        cur_pipelines.append(
            {'dag_id': pipeline['dag_id'],
             'dag_name': pipeline['dag_name']})
    return cur_pipelines


@app.get('/get_task_stage/{dag_id}')
async def get_service_stage(dag_id):
    """

    :param dag_id:
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
    # print(f'pipelines:{server.pipelines}')
    dag_id = int(dag_id)
    pipeline = server.find_pipeline_by_id(dag_id)
    if pipeline is None:
        print(f'id {dag_id} not exists in pipeline')
        return []

    task_name = server.get_pipeline_label(pipeline)

    for server_task in server.tasks:
        if server_task['name'] == task_name:
            return server_task['stage']

    LOGGER.warning(f'task name {task_name} error!')
    return []


@app.post('/install')
async def install_service(data=Body(...)):
    """
    body
    {
        "dag_id": (id),
        "image_list": ["", ""]
    }
    :return:
    {'msg': 'service start successfully'}
    {'msg': 'Invalid service name!'}
    """

    @timeout(60)
    def install_loop():
        _result = KubeHelper.apply_custom_resources(yaml_file, server.namespace)
        while not KubeHelper.check_pods_running(server.namespace):
            time.sleep(1)
        return _result

    data = json.loads(str(data, encoding='utf-8'))

    dag_id = int(data['dag_id'])
    images = data['image_list']

    pipeline = server.find_pipeline_by_id(dag_id)
    if pipeline is None:
        return {'state': 'fail', 'msg': '服务下装失败：流水线不存在'}

    task_name = server.get_pipeline_label(pipeline)

    cur_task = None

    for task in server.tasks:
        if task['name'] == task_name:
            cur_task = task
            break

    if cur_task is None:
        return {'state': 'fail', 'msg': '服务不存在'}

    yaml_file = os.path.join(server.templates_path, cur_task['yaml'])
    LOGGER.info(f'yaml_file: {yaml_file}')

    try:
        result = install_loop()
    except Exception as e:
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

    if KubeHelper.check_pods_running(server.namespace):
        for task in server.tasks:
            if KubeHelper.check_pod_name(task['word'], namespace=server.namespace):
                return [stage['stage_name'] for stage in task['stage']]
    else:
        return []


@app.get('/get_dag_workflows_api')
async def get_dag_workflows():
    """
    获取已有流水线
    [
                {
                    "dag_id":1,
                    "dag_name":"headup",
                    "dag":["face_detection","face_alignment"]
                },
                {
                    "dag_id":1,
                    "dag_name":"traffic",
                    "dag":["car_detection","plate_recognition"]
                },
                {
                    "dag_id":1,
                    "dag_name":"ixpe",
                    "dag":["ixpe_preprocess","ixpe_sr_and_pc","ixpe_edge_observe"]
                }

            ],
    :return:
    """

    return server.pipelines


@app.get('/get_all_service')
async def get_all_service():
    """
    获取所有容器（docker仓库里的所有）

    [
    {
        "service_name": "face_detection",
        "description": "人脸检测"
    },
    {
        "service_name": "car_detection"，
        "description": "车辆检测"
    }
]
    :return:
    """

    return server.services


@app.post('/update_dag_workflows_api')
def update_dag_workflows(data=Body(...)):
    """
    新增流水线
    body
    {
        "dag_name":"headup",
        "dag":["face_detection","face_alignment"]
    },
    :return:
        {'state':success/fail, 'msg':'...'}
    """
    # data = json.loads(str(data, encoding='utf-8'))
    pipeline_name = data['dag_name']
    pipeline = data['dag']

    if server.check_pipeline(pipeline):
        server.pipelines.append({
            'dag_id': NameCounter.get_name_counter(),
            'dag_name': pipeline_name,
            'dag': pipeline
        })
        return {'state': 'success', 'msg': '新增流水线成功'}
    else:
        return {'state': 'fail', 'msg': '新增流水线失败：非法流水线定义'}


@app.post('/delete_dag_workflow')
def delete_dag_workflow(data=Body(...)):
    """
    删除流水线
    body:
    {
        "dag_id":1
    }
    :return:
    {'state':success/fail, 'msg':'...'}
    """

    data = json.loads(str(data, encoding='utf-8'))
    dag_id = int(data['dag_id'])
    for index, pipeline in enumerate(server.pipelines):
        if pipeline['dag_id'] == dag_id:
            del server.pipelines[index]
            return {'state': 'success', 'msg': '删除流水线成功'}

    return {'state': 'fail', 'msg': '删除流水线失败：流水线不存在'}


@app.post('/datasource_config')
async def upload_datasource_config_file(file: UploadFile = File(...)):
    """
    body: file
    :return:
        {'state':success/fail, 'msg':'...'}
    """
    file_data = await file.read()
    with open('config.json', 'wb') as buffer:
        buffer.write(file_data)
    with open('config.json', 'r') as f:
        config = json.load(f)

    if server.check_datasource_config(config) and not server.check_datasource_exists(config):
        server.sources.append(config)
        return {'state': 'success', 'msg': '数据流配置成功'}
    else:
        return {'state': 'fail', 'msg': '数据流配置失败，请检查上传配置文件格式'}


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
        if service == 'null':
            return []
        info = KubeHelper.get_service_info(service_name=service, namespace=server.namespace)

        # TODO: bandwidth
        # resource_data = http_request(server.resource_url, method='GET')
        # # print(resource_data)
        # for single_info in info:
        #     single_info['bandwidth'] = f"{resource_data[single_info['hostname']]['bandwidth']:.2f}Mbps" if \
        #         resource_data[single_info['hostname']]['bandwidth'] != 0 else '-'
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
                    "importance": 4

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
    }
    :return:
    {'msg': 'service start successfully'}
    {'msg': 'Invalid service name!'}
    """

    data = json.loads(str(data, encoding='utf-8'))

    source_label = data['source_label']

    server.source_open = True
    server.source_label = source_label
    for source_id in server.get_source_id():
        server.task_results[source_id] = ResultQueue(20)

    server.is_get_result = True
    threading.Thread(target=server.run_get_result).start()

    time.sleep(2)

    return {'state': 'success', 'msg': '数据流打开成功'}


@app.post('/stop_service')
async def stop_service():
    """
    {'state':"success/fail",'msg':'...'}

    :return:
    """

    @timeout(120)
    def stop_loop():
        result = KubeHelper.delete_resources(server.namespace)
        while KubeHelper.check_pods_exist(server.namespace):
            time.sleep(1)
        return result

    try:
        result = stop_loop()
        server.is_get_result = False
    except Exception as e:
        logging.exception(e)
        result = False

    server.priority_queue_state = []
    server.queue_waiting_list = []

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
    server.is_get_result = False
    server.task_results = {}
    server.queue_results = None

    time.sleep(2)

    return {'state': 'success', 'msg': '数据流关闭成功'}


@app.get('/install_state')
async def get_install_state():
    """
    :return:
    {'state':'install/uninstall'}
    """

    state = 'install' if KubeHelper.check_pods_exist(server.namespace) else 'uninstall'
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
                return [{'id': camera['id'], 'label': camera['name']} for camera in source['camera_list']]
    else:
        return []


@app.get('/result_prompt')
async def get_result_prompt():
    """
    结果提示文字
    :return:
    {
        'visualizing_prompt': '...',
        'result_title_prompt':'...',
        'result_text_prompt': '...',
        'delay_text_prompt': '...',
    }
    """

    if KubeHelper.check_pods_running(server.namespace):
        for task in server.tasks:
            if KubeHelper.check_pod_name(task['word'], namespace=server.namespace):
                return {
                    'visualizing_prompt': task['visualizing_prompt'],
                    'result_title_prompt': task['result_title_prompt'],
                    'result_text_prompt': task['result_text_prompt'],
                    'delay_text_prompt': task['delay_text_prompt'],
                }
    else:
        return {'visualizing_prompt': '',
                'result_title_prompt': '',
                'result_text_prompt': '',
                'delay_text_prompt': '',
                }


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
    if not server.source_open:
        return {}
    ans = {}
    for source_id in server.get_source_id():
        ans[source_id] = server.task_results[source_id].get_results()

    return ans


@app.get('/download_log')
def download_log():
    """

    :return:
    file
    """

    if not os.path.exists(server.log_file):
        with open(server.log_file, 'w'):
            pass
    file_name = server.log_file
    return FileResponse(
        file_name,
        filename=f'Auto-Edge_log_{int(time.time())}.txt'
    )


def main():
    uvicorn.run(app, host='0.0.0.0', port=8910)


if __name__ == '__main__':
    main()
