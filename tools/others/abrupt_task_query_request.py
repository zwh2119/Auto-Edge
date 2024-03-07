import requests
import argparse

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


def abrupt_query(task_type, task_num):
    url = 'http://114.212.81.11:39400/task'
    response = http_request(url, method='POST', json={'task_type': task_type, 'cycle_num': task_num})
    if response is not None and response['success']:
        print(f'query {task_type} for {task_num} tasks..')
    else:
        print(f'query {task_type} failed..')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--task_type', default='human',help='task type, car or human')
    parser.add_argument('--number', default=10, type=int, help='number of query tasks')

    args = parser.parse_args()

    abrupt_query(args.task_type, args.number)
