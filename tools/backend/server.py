import base64
import datetime
import threading

import eventlet
import numpy as np

eventlet.monkey_patch()

import json
import os
import time

import uvicorn
from fastapi import FastAPI, Body, Request, File, UploadFile

from fastapi.middleware.cors import CORSMiddleware
import requests

from kube_helper import KubeHelper
import yaml
import logging
import queue
import cv2
import io
import wave
import librosa
from PIL import Image

import matplotlib.pyplot as plt


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
            self.__queue.put(result)
            if 0 < self.__length < self.__queue.qsize():
                self.__queue.get()

    def get_results(self):
        results = []
        while not self.__queue.empty():
            results.append(self.__queue.get())
        return results

    def clear_results(self):
        self.get_results()


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
    except Exception as e:
        logging.exception(e)


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
                'namespace': 'auto-edge-car',
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
                'namespace': 'auto-edge-audio',
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
                'namespace': 'auto-edge-imu',
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
                'namespace': 'auto-edge-edge-eye',
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

        self.total_sources = [
            {
                "source_label": "car",
                "source_name": "交通监控摄像头",
                "source_type": "视频流",
                "camera_list": [
                    {
                        'id': 'car_video_source1',
                        "name": "交通摄像头1",
                        "url": "rtsp://192.168.1.51/video0",
                        "describe": "高速公路监控摄像头",
                        "resolution": "1080p",
                        "fps": "25fps",
                        "importance": 7

                    },
                    {
                        'id': 'car_video_source2',
                        "name": "交通摄像头2",
                        "url": "rtsp://192.168.1.55/video1",
                        "describe": "十字路口监控摄像头",
                        "resolution": "1080p",
                        "fps": "30fps",
                        "importance": 2
                    }
                ]

            },
            {
                "source_label": "audio",
                "source_name": "音频数据流",
                "source_type": "音频流",
                "camera_list": [
                    {
                        'id': 'audio_source1',
                        "name": "音频流1",
                        "url": "http://192.168.2.22:3381/audio",
                        "describe": "音频来源1",
                        "importance": 7

                    },
                    {
                        'id': 'audio_source2',
                        "name": "音频流2",
                        "url": "http://192.168.2.22:3382/audio",
                        "describe": "音频来源2",
                        "importance": 2
                    }
                ]

            },
            {
                "source_label": "imu",
                "source_name": "惯性数据流",
                "source_type": "IMU流",
                "camera_list": [
                    {
                        'id': 'imu_source1',
                        "name": "IMU流1",
                        "url": "http://192.168.2.11:3000/imu",
                        "describe": "IMU场景1",
                        "importance": 7

                    },
                    {
                        'id': 'imu_source2',
                        "name": "IMU流2",
                        "url": "http://192.168.2.91:3001/imu",
                        "describe": "IMU场景2",
                        "importance": 2
                    }
                ]

            },
            {
                "source_label": "edge-eye",
                "source_name": "工厂摄像头",
                "source_type": "视频流",
                "camera_list": [
                    {
                        'id': 'edge_eye_video_source1',
                        "name": "工厂摄像头1",
                        "url": "rtsp://192.168.1.67/video0",
                        "describe": "工厂1",
                        "resolution": "1080p",
                        "fps": "25fps",
                        "importance": 7

                    },
                    {
                        'id': 'edge_eye_video_source2',
                        "name": "工厂摄像头2",
                        "url": "rtsp://192.168.1.83/video1",
                        "describe": "工厂2",
                        "resolution": "1080p",
                        "fps": "25fps",
                        "importance": 2
                    }
                ]

            },

        ]

        self.sources = []

        self.services = [
            'audio-classification',
            'audio-sampling',
            'car-detection',
            'edge-eye-stage1',
            'edge-eye-stage2',
            'edge-eye-stage3',
            'imu-trajectory-sensing'
        ]

        self.pipelines = []

        self.legal_pipelines = {
            'road-detection': ['car-detection'],
            'audio': ['audio-sampling', 'audio-classification'],
            'imu': ['imu-trajectory-sensing'],
            'edge-eye': ['edge-eye-stage1', 'edge-eye-stage2', 'edge-eye-stage3']
        }

        self.audio_class = [
            "空调运转声",
            "汽车喇叭声",
            "嘻戏打闹声",
            "狗叫声",
            "钻孔声",
            "引擎怠速声",
            "枪声",
            "挖掘机工作声",
            "警报声",
            "流行音乐声"
        ]

        self.devices = {
            'http://114.212.81.11:39200/submit_task': 'cloud',
            'http://192.168.1.2:39200/submit_task': 'edge1',
            'http://192.168.1.4:39200/submit_task': 'edge2',
        }

        self.latest_namespace = 'auto-edge'

        self.time_ticket = 0

        self.templates_path = '/home/hx/zwh/Auto-Edge/templates'
        self.free_task_url = 'http://114.212.81.11:39400/task'

        self.result_url = 'http://114.212.81.11:39500/result'
        self.result_file_url = 'http://114.212.81.11:39500/file'

        self.resource_url = 'http://114.212.81.11:39400/resource'
        self.parameters_url = 'http://114.212.81.11:39400/parameters'

        self.source_open = False

        self.source_label = ''

        self.save_logs_path = ''

        self.task_results = {}
        self.queue_results = {}

        self.is_get_result = False

        self.free_open = {}
        self.is_free_result = {}
        self.free_start = {}
        self.free_end = {}
        self.free_duration = {}
        self.free_result = {}
        self.free_result_save = {}

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

    def find_latest_task_namespace(self):
        return self.latest_namespace

    def create_new_namespace(self, task_namespace):
        # self.latest_namespace = 'mid-' + task_namespace + '-' + str(NameCounter.get_name_counter())
        # KubeHelper.create_namespace(self.latest_namespace)

        return self.latest_namespace

    def clear_latest_namespace(self):
        pass

    def run_get_result(self):
        time_ticket = 0
        while self.is_get_result:
            response = http_request(self.result_url, method='GET', json={'time_ticket': time_ticket, 'size': 0})
            if response:
                time_ticket = response["time_ticket"]
                results = response['result']
                for result in results:
                    source_id = result['source']
                    task_id = result['task']
                    delay = self.cal_pipeline_delay(result['pipeline'])

                    if delay > 3:
                        print(f'task delay of {delay} filtered!')
                        continue

                    priority_trace = self.get_pipeline_priority(result['priority'])
                    task_result = result['obj_num']

                    task_type = result['task_type']
                    content = result['content']
                    file_path = self.get_file_result(source_id, task_id)
                    if task_type == 'edge-eye' and 'frame' not in content:
                        print('edge eye not have frame, skip..')
                        continue
                    base64_data = self.get_base64_data(file_path, task_type, task_result, content)
                    os.remove(file_path)
                    source_id_text = self.source_id_num_2_id_text(source_id)
                    self.task_results[source_id_text].save_results([{
                        'taskId': task_id,
                        'result': task_result,
                        'delay': delay,
                        'visualize': base64_data
                    }])
                    self.queue_results[source_id_text].save_results([{
                        'taskId': task_id,
                        'priorityTrace': priority_trace
                    }])

                    if source_id_text in self.free_open and self.free_open[source_id_text] \
                            and not self.is_free_result[source_id_text]:
                        self.free_result[source_id_text].save_results([
                            {'taskId': task_id,
                             'result': task_result,
                             'delay': delay, }
                        ])

            time.sleep(1)

    def check_datasource_config(self, config):
        pass

    def cal_pipeline_delay(self, pipeline):
        delay = 0
        print('delay:  ', end='')
        for i, stage in enumerate(pipeline):
            execute = stage['execute_data']
            if 'transmit_time' in execute:
                delay += execute['transmit_time']
            if 'service_time' in execute:
                delay += execute['service_time']
                print(f'stage{i}->{execute["service_time"]:.2f}s  ', end='')
        print(f'total:->{delay:.2f}s')
        return delay

    def get_file_result(self, source_id, task_id):
        file_name = f'file_{source_id}_{task_id}'
        response = http_request(self.result_file_url, method='GET', no_decode=True,
                                json={'source_id': source_id, 'task_id': task_id},
                                stream=True)
        with open(file_name, 'wb') as file_out:
            for chunk in response.iter_content(chunk_size=8192):
                file_out.write(chunk)
        return file_name

    def get_pipeline_priority(self, priority):
        trace = []
        for stage in priority:
            trace.append({
                'urgency': stage['urgency'],
                'importance': stage['importance'],
                'priority': stage['priority']
            })
        return trace

    def source_id_num_2_id_text(self, source_id):
        source_id_text_list = self.get_source_id()
        return source_id_text_list[source_id]

    def get_base64_data(self, file, task_type, result, content):
        image = None

        if task_type == 'car':
            video_cap = cv2.VideoCapture(file)
            success, image = video_cap.read()
            image = self.draw_bboxes(image, content[0])
        elif task_type == 'imu':
            img_path = self.draw_imu_trajectory(content[0])
            image = cv2.imread(img_path)

        elif task_type == 'audio':
            f = wave.open(file, "r")
            params = f.getparams()
            nchannels, sampwidth, framerate, nframes = params[:4]
            data = f.readframes(nframes)
            img_path = self.draw_audio_spec(data, framerate, nchannels, self.audio_class[result])
            image = cv2.imread(img_path)
        elif task_type == 'edge-eye':
            frame = content['frame']
            image = self.decode_image(frame)
        else:
            assert None, f'Invalid task type of {task_type}'
        image = cv2.resize(image, (320, 240))
        base64_str = cv2.imencode('.jpg', image)[1].tobytes()
        base64_str = base64.b64encode(base64_str)
        base64_str = bytes('data:image/jpg;base64,', encoding='utf8') + base64_str
        return base64_str

    def decode_image(self, encoded_img_str):
        # 将 Base64 编码的字符串转换回 bytes
        encoded_img_bytes = base64.b64decode(encoded_img_str)
        # 解码图像
        decoded_img = cv2.imdecode(np.frombuffer(encoded_img_bytes, np.uint8), cv2.IMREAD_COLOR)
        return decoded_img

    def draw_bboxes(self, frame, bbox):
        for x_min, y_min, x_max, y_max in bbox:
            cv2.rectangle(frame, (int(x_min), int(y_min)), (int(x_max), int(y_max)), (0, 255, 0), 4)
        return frame

    def draw_imu_trajectory(self, input_data):
        process_data = np.array(input_data)
        np.save(f'debug/{int(time.time())}.npy', process_data)
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.plot3D(process_data[:, 0], process_data[:, 1], process_data[:, 2])

        plt.savefig('imu.png', bbox_inches='tight', pad_inches=0.1)
        plt.close(fig)
        return 'imu.png'

    def draw_audio_spec(self, data, framerate, nchannels, result):
        # TODO: plot result class type on picture

        def cal_norm(nparray):
            # [-1, 1]
            return 2 * (nparray - np.min(nparray)) / (np.max(nparray) - np.min(nparray)) - 1

        databuffer = np.frombuffer(data, dtype=np.short)
        if nchannels == 2:
            databuffer = (databuffer[::2] + databuffer[1::2]) / 2

        window_size = int(0.05 * framerate)
        overlap = int(window_size * (1 - 0.75))
        n_fft = 4096

        stft = librosa.stft(databuffer.astype(np.float32), n_fft=n_fft, hop_length=overlap, win_length=window_size)

        # 转换为分贝 (dB) 单位
        log_spectrogram = librosa.amplitude_to_db(np.abs(stft))
        # 归一化为 [-1, 1]
        log_spectrogram = cal_norm(log_spectrogram)

        # 画出频谱图
        librosa.display.specshow(log_spectrogram, sr=framerate, win_length=window_size, hop_length=overlap,
                                 x_axis='time', y_axis='linear')
        # 添加颜色条
        plt.colorbar(format='%+2.0f', ticks=[-1, 1])

        plt.savefig('audio.png')
        plt.close()

        return 'audio.png'

    def timer(self, duration, source_label):
        self.free_start[source_label] = f'{datetime.datetime.now():%Y-%m-%d %H:%M:%S}'
        time.sleep(duration)
        self.free_end[source_label] = f'{datetime.datetime.now():%Y-%m-%d %H:%M:%S}'
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
        if source_label in self.free_result:
            del self.free_result[source_label]
        if source_label in self.free_result_save:
            del self.free_result_save[source_label]

    def run_manage_namespace(self):
        while True:
            namespace_list = KubeHelper.list_namespaces('mid')
            for namespace in namespace_list:
                if not KubeHelper.check_pods_exist(namespace):
                    KubeHelper.delete_namespace(namespace)
            time.sleep(5)


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
    显示已有流水线 {dag_id:dag_name}
    """
    cur_pipelines = []
    for pipeline in server.pipelines:
        cur_pipelines.append({pipeline['dag_id']: pipeline['dag_name']})
    return cur_pipelines


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
        "task_name": (id),
        "image_list": ["", ""]
    }
    :return:
    {'msg': 'service start successfully'}
    {'msg': 'Invalid service name!'}
    """
    data = json.loads(str(data, encoding='utf-8'))

    dag_id = data['task_name']
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
    print(f'yaml_file: {yaml_file}')

    namespace = server.create_new_namespace(cur_task['namespace'])

    try:
        with eventlet.Timeout(60, True):
            result = KubeHelper.apply_custom_resources(yaml_file, namespace)
            while not KubeHelper.check_pods_running(namespace):
                time.sleep(1)

    except eventlet.timeout.Timeout as e:
        logging.exception(e)
        result = False

    server.newest_task = cur_task['name']

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

    namespace = server.find_latest_task_namespace()
    if namespace == '':
        return []
    if KubeHelper.check_pods_running(namespace):
        for task in server.tasks:
            if KubeHelper.check_pod_name(task['word'], namespace=namespace):
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
    ["face_detection","face_alignment","car_detection","helmet_detection","ixpe_preprocess","ixpe_sr_and_pc","ixpe_edge_observe"]
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
    data = json.loads(str(data, encoding='utf-8'))
    pipeline_name = data['dag_name']
    pipeline = data['dag']

    if server.check_pipeline(pipeline):
        server.pipelines.append({
            'dag_id': NameCounter.get_name_counter(),
            'dag_name': pipeline_name,
            'dag': pipeline
        })
        return {'state': 'success', 'msg': '新增流水线成功¬'}
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
    for pipeline in server.pipelines:
        if pipeline['dag_id'] == dag_id:
            return {'state': 'success', 'msg': '删除流水线成功'}

    return {'state': 'fail', 'msg': '删除流水线失败：流水线不存在'}


@app.post('/datasource_config')
async def upload_datasource_config_file(file: UploadFile = File(...)):
    # TODO
    """
    body: file
    :return:
        {'state':success/fail, 'msg':'...'}
    """
    file_data = await file.read()
    config = json.load()

    if server.check_datasource_config(config):
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
        namespace = server.find_latest_task_namespace()
        info = KubeHelper.get_service_info(service_name=service, namespace=namespace)
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
    # TODO: 增加提交importance到调度器
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
    delay_constraint = float(data['delay_cons'])
    acc_constraint = float(data['acc_cons'])
    urgency_weight = float(data['urgency'])
    importance_weight = float(data['importance'])

    http_request(server.parameters_url, method='POST', json={'user_constraint': delay_constraint,
                                                             'urgency_weight': urgency_weight,
                                                             'importance_weight': importance_weight})
    server.source_open = True
    server.source_label = source_label
    for source_id in server.get_source_id():
        server.task_results[source_id] = ResultQueue(10)
        server.queue_results[source_id] = ResultQueue(10)

    server.is_get_result = True
    threading.Thread(target=server.run_get_result).start()

    return {'state': 'success', 'msg': '数据流打开成功'}


@app.post('/stop_service')
async def stop_service():
    """
    {'state':"success/fail",'msg':'...'}

    :return:
    """
    namespace = server.find_latest_task_namespace()
    try:
        with eventlet.Timeout(120, True):
            result = KubeHelper.delete_resources(namespace)
            while KubeHelper.check_pods_exist(namespace):
                time.sleep(1)

        server.is_get_result = False

    except eventlet.timeout.Timeout as e:
        logging.exception(e)
        result = False
    except Exception as e:
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
    server.is_get_result = False
    server.task_results = {}
    server.queue_results = {}

    return {'state': 'success', 'msg': '数据流关闭成功'}


@app.get('/install_state')
async def get_install_state():
    """
    :return:
    {'state':'install/uninstall'}
    """
    namespace = server.find_latest_task_namespace()
    if namespace == '':
        state = 'uninstall'
    else:
        state = 'install' if KubeHelper.check_pods_exist(namespace) else 'uninstall'
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


@app.get('/pipeline_info')
async def get_pipeline_info():
    # TODO
    """
    {
        'priority_num': 10,
        'stage': [stage_name1,stage_name2]
    }

    """
    namespace = server.find_latest_task_namespace()
    if namespace == '':
        return []
    if KubeHelper.check_pods_running(namespace):
        for task in server.tasks:
            if KubeHelper.check_pod_name(task['word'], namespace=namespace):
                return [stage['stage_name'] for stage in task['stage']]
    else:
        return []


@app.get('/result_prompt')
async def get_result_prompt():
    # TODO
    """
    结果提示文字
    :return:
    {
        'visualizing_prompt': '...',
        'result_title_prompt':'...'，
        'result_text_prompt': '...',
        'delay_text_prompt': '...',
        'free_task_menu':['最大值','平均值']
    }
    """
    namespace = server.find_latest_task_namespace()
    if namespace == '':
        return {'prompt': ''}
    if KubeHelper.check_pods_running(namespace):
        for task in server.tasks:
            if KubeHelper.check_pod_name(task['word'], namespace=namespace):
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
    if not server.source_open:
        return {}
    ans = {}
    for source_id in server.get_source_id():
        ans[source_id] = server.task_results[source_id].get_results()

    # print(f'task result: {ans}')
    return ans


@app.get('/queue_result')
async def get_queue_result():
    # TODO
    """

    [
        # stage1
        [
            # priority queue 1
            [{
            source_id: 1,
            task_id: 1,
            importance: 1
            urgency: 1
            },{},{},{}],
            [],
            [],
            [],
            []
        ],
        # stage2
        [
            [],
            [],
            [],
            [],
            []

        ]
    ]
    :return:
    """
    ans = {}
    for source_id in server.get_source_id():
        ans[source_id] = server.queue_results[source_id].get_results()

    return ans


@app.post('/start_free_task')
async def start_free_task(data=Body(...)):
    # TODO
    """
    body
        {
            'source_label':'...',
            'free_type': '最大值',
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
    server.free_result[source_label] = ResultQueue()
    server.free_result_save[source_label] = {}
    threading.Thread(target=server.timer, args=(duration, source_label)).start()

    return {'state': 'success', 'msg': '启动自由任务成功'}


@app.get('/free_state/{source}')
async def get_free_state(source):
    """

    :return:
    {
        'state':0/1/2,
        'duration':20
    }
    """
    if source not in server.free_open or not server.free_open[source]:
        return {'state': 0}
    elif not server.is_free_result[source]:
        return {'state': 1, 'duration': server.free_duration[source]}
    else:
        return {'state': 2, 'duration': server.free_duration[source]}


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
    # TODO
    """

    :param source:
    :return:
    {
        'state':0/1/2,(是否有结果)
        0：无任务
        1：正在执行
        2：有结果
        'task_info':
        [
            {name:任务数量, value:20},(result)
        ],

        'delay':[
            时延数据
        ],

        'start_time': 'xxx',
        'end_time': 'xxx'

    }
    """
    if source not in server.free_open or not server.free_open[source]:
        return {'state': 0}
    if source not in server.is_free_result or not server.is_free_result[source]:
        return {'state': 1}
    else:

        results = server.free_result[source].get_results()
        if not results:
            delay = server.free_result_save[source]['delay']
            task_info = server.free_result_save[source]['task_info']
        else:
            delay = []
            task_info = []
            result_count = []
            for result in results:
                delay.append(result['delay'])
                result_count.append(result['result'])

            task_info.append({'name': '任务数量', 'value': len(result_count)})

            if server.source_label == 'car':
                task_info.append({'name': '车流峰值', 'value': int(max(result_count))})
                task_info.append({'name': '车流平均值', 'value': int(np.mean(result_count))})
            elif server.source_label == 'audio':
                task_info.append({'name': '音频最多识别类别',
                                  'value': server.audio_class[max(result_count, key=result_count.count)]})
                task_info.append({'name': '音频最大识别次数',
                                  'value': max([result_count.count(x) for x in set(result_count)])})
                task_info.append({'name': '音频平均识别次数',
                                  'value': int(np.mean([result_count.count(x) for x in set(result_count)]))})
            elif server.source_label == 'imu':
                task_info.append({'name': '轨迹长度最大值', 'value': max(result_count)})
                task_info.append({'name': '轨迹长度平均值', 'value': int(np.mean(result_count))})
            elif server.source_label == 'edge-eye':
                pass

            server.free_result_save[source]['delay'] = delay
            server.free_result_save[source]['task_info'] = task_info

        return {'state': 2,
                'start_time': server.free_start[source],
                'end_time': server.free_end[source],
                'delay': delay,
                'task_info': task_info
                }


@app.get('/download_log')
def download_log():
    # TODO
    """

    :return:
    file
    """


def main():
    # threading.Thread(target=server.run_manage_namespace).start()
    uvicorn.run(app, host='0.0.0.0', port=8910)


if __name__ == '__main__':
    main()
