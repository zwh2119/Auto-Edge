import shutil
import time
import iperf3
import psutil
import threading

import eventlet

from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form

from fastapi.routing import APIRoute
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import uvicorn
import requests

import argparse
import json


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



def iperf_server(port):
    server = iperf3.Server()
    server.port = port
    print('Running iperf3 server: {0}:{1}'.format(server.bind_address, server.port))

    while True:
        try:
            result = server.run()
        except Exception as e:
            continue

        if result.error:
            print(result.error)


class MonitorServer:
    def __init__(self, iperf3_server):

        self.bandwidth = 0
        self.monitor_interval = 1
        self.iperf3_server = iperf3_server

        self.app = FastAPI(routes=[
            APIRoute('/test_task',
                     self.deal_response,
                     response_class=JSONResponse,
                     methods=['POST']
                     ),
        ], log_level='trace', timeout=6000)

        self.app.add_middleware(
            CORSMiddleware, allow_origins=["*"], allow_credentials=True,
            allow_methods=["*"], allow_headers=["*"],
        )

        if self.iperf3_server:
            self.iperf3_port = 9910
            self.run_iperf_server()
            self.run_fastapi_server()
        else:
            self.iperf3_port = 9910

    def deal_response(self, file: UploadFile = File(...), data: str = Form(...)):
        data = json.loads(data)
        start_time = data['time']
        with open(file.filename, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)
            del file
        return {'time': time.time() - start_time}

    def send_package(self):
        file_path = '720p_fig.png'
        response = http_request(url='http://114.212.81.11:8910/test_task', method='POST',
                                data={'data': json.dumps({'time': time.time()})},
                                files={'file': (file_path, open(file_path, 'rb'), 'multipart/form-data')}
                                )
        if response:
            return response['time']

    def run(self):
        if self.iperf3_server:
            return
        while True:
            bandwidth = self.get_bandwidth()
            delay = self.send_package()
            if bandwidth is None or delay is None:
                print(f'skip! bandwidth:{bandwidth},delay:{delay}')
                continue
            print(f'bandwidth: {bandwidth*1000:.4f}Kbps, delay: {delay:.4f}s')

            with open('bandwidth_delay.txt', 'a') as f:
                f.write(f'{bandwidth*1000:.4f}  {delay:.4f}\n')

            # time.sleep(self.monitor_interval)

    def get_bandwidth(self):

        client = iperf3.Client()
        client.duration = 1
        client.server_hostname = '114.212.81.11'
        client.port = self.iperf3_port
        client.protocol = 'tcp'

        eventlet.monkey_patch()
        try:
            with eventlet.Timeout(2, True):
                result = client.run()

            if result.error:
                print(f'resource monitor iperf3 error: {result.error}')

            self.bandwidth = result.sent_Mbps

            return self.bandwidth

        except eventlet.timeout.Timeout:
            print('connect to server timeout!')

    def run_iperf_server(self):
        port = self.iperf3_port
        threading.Thread(target=iperf_server, args=(port,)).start()

    def run_fastapi_server(self):
        threading.Thread(target=self.fastapi_server).start()

    def fastapi_server(self):
        uvicorn.run(self.app, host='0.0.0.0', port=8910)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', action='store_true')
    args = parser.parse_args()
    monitor = MonitorServer(args.server)
    monitor.run()
