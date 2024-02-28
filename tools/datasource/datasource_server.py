import os
import subprocess
import signal
import time

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


def start_script(command):
    process = subprocess.Popen(command, shell=True, preexec_fn=os.setsid)
    return process


def stop_script(process):
    os.killpg(os.getpgid(process.pid), signal.SIGTERM)


class DataSource:
    def __init__(self):
        self.source_label = ''
        self.source_open = False

        self.process_list = []

        self.source_url = 'http://114.212.81.11:8910/query_state'

    def open_datasource(self, modal):
        if self.source_open:
            return

        print(f'open datasource {modal}')

        if modal == 'car':
            commands = ['bash push.sh video/traffic-mid0.mp4 rtsp://127.0.0.1/video0',
                        'bash push.sh video/traffic-mid1.mp4 rtsp://127.0.0.1/video1']
        elif modal == 'audio':
            commands = ['python3 audio_datasource.py --dataset audio/1 --port 6000',
                        'python3 audio_datasource.py --dataset audio/2 --port 6001']
        elif modal == 'imu':
            commands = ['python3 imu_datasource.py --dataset imu/1 --port 5000',
                        'python3 imu_datasource.py --dataset imu/2 --port 5001']
        elif modal == 'edge-eye':
            commands = ['bash push.sh video/ixpe0.mp4 rtsp://127.0.0.1/eye0',
                        'bash push.sh video/ixpe1.mp4 rtsp://127.0.0.1/eye1']
        else:
            print(f'datasource of {modal} not exists!')
            return

        for command in commands:
            process = start_script(command)
            self.process_list.append(process)

        self.source_label = modal
        self.source_open = True

    def close_datasource(self):
        if not self.source_open:
            return

        print('close datasource')

        for process in self.process_list:
            stop_script(process)

        self.source_label = ''
        self.source_open = False

    def run(self):
        while True:
            response = http_request(self.source_url, method='GET')
            if response:
                if response['state']:
                    self.open_datasource(modal=response['source_label'])
                else:
                    self.close_datasource()
            else:
                self.close_datasource()
            time.sleep(2)


def main():
    server = DataSource()
    server.run()


if __name__ == '__main__':
    main()
