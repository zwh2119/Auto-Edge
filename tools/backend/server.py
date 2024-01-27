from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form

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
                     methods=['GET']
                     ),
            APIRoute('/free',
                     self.start_free_task,
                     response_class=JSONResponse,
                     methods=['POST']
                     ),
        ], log_level='trace', timeout=6000)

        self.app.add_middleware(
            CORSMiddleware, allow_origins=["*"], allow_credentials=True,
            allow_methods=["*"], allow_headers=["*"],
        )

        self.tasks = [{'road-detection': '交通路面监控'},
                      {'audio': '音频识别'},
                      {'imu': '惯性轨迹感知'},
                      {'edge-eye': '工业视觉纠偏'}]

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
        return self.tasks

    def start_task(self, service_name):
        pass


    def get_execute_result(self):
        pass

    def start_free_task(self, service_name, time):
        pass


if __name__ == '__main__':
    pass
