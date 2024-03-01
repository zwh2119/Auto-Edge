import time

import requests
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


if __name__ == '__main__':
    response = http_request(url='http://114.212.81.11:1234/test_upload', method='POST',
                 data={'data': json.dumps({'test':'this is test data'})},
                 files={'file': ('test_file.py', open('yolov5s.pt', 'rb'), 'multipart/form-data')}
                 )
    print(response)

    time.sleep(3)

    http_request(url='http://114.212.81.11:1234/test_upload', method='POST',
                 data={'data': json.dumps({'test':'this is test data'})},
                 files={'file': ('test_file.py', '', 'multipart/form-data')}
                 )
    print(response)

