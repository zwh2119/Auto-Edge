import time

import requests
from RainbowPrint import RainbowPrint as rp


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


def print_result():
    pass


if __name__ == '__main__':

    time_slot = 0
    request_size = 10
    url = 'http://114.212.81.11:9500/result'
    while True:
        time.sleep(1)
        res = http_request(url, json={'time_ticket': time_slot, "size": request_size})
        if res is not None and res['size'] > 0:
            pass
