import time

import requests


class PrintColors:
    RED = "\033[1;31m"  # 红色
    RED_3 = "\033[4;31m"  # 红色  带下划线
    PURPLE = "\033[1;35m"  # 紫色
    CYAN = "\033[1;36m"  # 青蓝色
    END = '\033[0m'


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
        else:
            return None
    except Exception as e:
        return None


def print_result(result):
    delay = 0
    for stage in result['pipeline']:
        execute = stage['execute_data']
        if 'transmit_time' in execute:
            delay += execute['transmit_time']
        if 'service_time' in execute:
            delay += execute['service_time']

    device = {'192.168.1.2': 'edge1', '192.168.1.4': 'edge2', '114.212.81.11': 'cloud'}
    execute_device = ''
    for i, stage in enumerate(result["pipeline"][:-1]):
        addr = stage["execute_address"]
        for ip in device:
            if ip in addr:
                if i != 0:
                    execute_device += ','
                execute_device += device[ip]
                break

    print(PrintColors.RED + '[source:{:>1d} task:{:>3d}]   '.format(result["source"], result["task"]) + PrintColors.END,
          end='')
    print('result(audio type):{}   '.format(result["obj_num"]), end='')

    print(f'execute:{execute_device}    ', end='')
    print(PrintColors.RED_3 + 'delay:{:.2f}s'.format(delay) + PrintColors.END, end='')
    print()

    priority = result['priority']

    print(
        f'              audio sampling:        importance:{priority[0]["importance"]}, urgency:{priority[0]["urgency"]} -> priority:{priority[0]["priority"]}')
    print(
        f'              audio classification:  importance:{priority[1]["importance"]}, urgency:{priority[1]["urgency"]} -> priority:{priority[1]["priority"]}')

    # print(result['pipeline'])
    # print(result)
    print('-----------------------------------------------------------------')


if __name__ == '__main__':

    time_slot = 0
    request_size = 10
    url = 'http://114.212.81.11:39500/result'
    while True:
        time.sleep(1)
        res = http_request(url, json={'time_ticket': time_slot, "size": request_size})
        if res is not None:
            time_slot = int(res['time_ticket'])
            for result in res['result']:
                print_result(result)
