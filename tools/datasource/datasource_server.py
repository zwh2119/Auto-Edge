import requests


class DataSource:
    def __init__(self):
        self.source_label = ''
        self.source_open = False

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


def main():
    pass


if __name__ == '__main__':
    main()
