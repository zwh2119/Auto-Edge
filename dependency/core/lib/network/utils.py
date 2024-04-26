import re


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


def find_all_ips(text):
    """
    :param text: 文本
    :return: 返回ip列表
    """
    ips = re.findall(r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b",
                     text)

    return ips
