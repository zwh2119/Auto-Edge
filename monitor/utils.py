import socket
from kubernetes import client, config

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