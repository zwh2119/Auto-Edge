import os
import time

import uvicorn
from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form, Body, Request

from fastapi.routing import APIRoute
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from kubernetes import client, config
import requests

app = FastAPI()


@app.get('/task')
async def get_all_task():
    """
    参考server_old
    :return:
    """
    pass


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
    pass


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
      {
                "192.168.56.102:7000": {
                    "0": {
                        "type": "traffic flow"
                    },
                    "1": {
                        "type": "people indoor"
                    },
                    "3":{
                      "type":"会议室开会"
                    },
                },
                "192.168.56.102:8000": {
                    "0": {
                        "type": "traffic flow"
                    },
                    "1": {
                        "type": "people indoor"
                    }
                },
                "192.168.56.102:9000": {
                    "0": {
                        "type": "traffic flow"
                    },
                    "1": {
                        "type": "people indoor"
                    }
                },
            }
    :return:
    """
    pass


@app.post("/query/submit_query")
def submit_task():
    """
    body
    {
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
