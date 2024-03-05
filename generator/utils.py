import time
import socket
from kubernetes import client, config
import cv2
import base64

def record_time(data: dict, time_sign: str):
    if time_sign in data:
        start_time = data[time_sign]
        end_time = time.time()
        del data[time_sign]
        return data, end_time - start_time
    else:
        data[time_sign] = time.time()
        return data, -1


def text2resolution(text: str):
    resolution_dict = {'1080p': (1920, 1080),
                       '720p': (1280, 720),
                       '360p': (640, 360)}

    assert text in resolution_dict
    return resolution_dict[text]


def resolution2text(resolution: tuple):
    resolution_dict = {(1920, 1080): '1080p',
                       (1280, 720): '720p',
                       (640, 360): '360p'}
    assert resolution in resolution_dict
    return resolution_dict[resolution]


def get_merge_address(ip, protocal='http', port=None, path=None):
    """
    merge address from {protocal, ip, port, path}
    eg: http://127.0.0.1:9000/submit
    """

    port_divider = '' if port is None else ':'
    path_divider = '' if path is None else '/'

    port = '' if port is None else port
    path = '' if path is None else path

    return f'{protocal}://{ip}{port_divider}{port}{path_divider}{path}'


def get_host_ip():
    """
    get ip of current local host
    """

    ip = '127.0.0.1'
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        pass
    finally:
        s.close()

    return ip


def get_nodes_info():
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


def encode_image(img):
    # 编码图像
    _, encoded_img = cv2.imencode('.jpg', img)
    encoded_img_bytes = encoded_img.tobytes()
    # 转换为 Base64 编码的字符串
    encoded_img_str = base64.b64encode(encoded_img_bytes).decode('utf-8')
    return encoded_img_str
