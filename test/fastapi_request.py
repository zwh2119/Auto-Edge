import asyncio
import aiohttp

import requests
import tenacity
from tenacity import retry

import logging
import colorlog


class Logger:
    """
    Deafult logger in sedna
    Args:
        name(str) : Logger name, default is 'sedna'
    """

    def __init__(self, name: str = ''):
        self.logger = logging.getLogger(name)

        self.format = colorlog.ColoredFormatter(
            '%(log_color)s[%(asctime)-15s] %(filename)s(%(lineno)d)'
            ' [%(levelname)s]%(reset)s - %(message)s', )

        self.handler = logging.StreamHandler()
        self.handler.setFormatter(self.format)

        self.logger.addHandler(self.handler)
        self.logLevel = 'INFO'
        # self.logger.setLevel(level='trace')
        self.logger.propagate = False


LOGGER = Logger().logger


@retry(stop=tenacity.stop_after_attempt(5),
       retry=tenacity.retry_if_result(lambda x: x is None),
       wait=tenacity.wait_fixed(3))
def http_request(
        url,
        method=None,
        timeout=None,
        binary=True,
        no_decode=False,
        **kwargs
):
    _maxTimeout = timeout if timeout else 300
    _method = "GET" if not method else method
    try:
        response = requests.request(method=_method, url=url, **kwargs)
        if response.status_code == 200:
            if no_decode:
                return response
            else:
                return (response.json() if binary else
                        response.content.decode("utf-8"))
        elif 200 < response.status_code < 400:
            LOGGER.info(f"Redirect_URL: {response.url}")
        LOGGER.warning(
            f'Get invalid status code \
                {response.status_code} in request {url}')

    except (ConnectionRefusedError, requests.exceptions.ConnectionError):
        LOGGER.warning(f'Connection refused in request {url}')
    except requests.exceptions.HTTPError as err:
        LOGGER.warning(f"Http Error in request {url} : {err}")
    except requests.exceptions.Timeout as err:
        LOGGER.warning(f"Timeout Error in request {url} : {err}")
    except requests.exceptions.RequestException as err:
        LOGGER.warning(f"Error occurred in request {url} : {err}")


async def request_func(num):
    print(f'{num} start')
    await http_request(url='http://127.0.0.1:3387/test', method="GET", json={'number': num})
    print(f'{num} over')


## 3_async_aiohttp.py ##
import time
import asyncio
import aiohttp
import requests


async def get(i):
    print(time.strftime('%X'), 'start', i)
    async with aiohttp.ClientSession() as session:
        async with session.get('http://127.0.0.1:3387/test', json={'number': i}) as response:
            html = await response.text()
    print(time.strftime('%X'), 'end', i, f' result: {html}')


async def post(i, image):
    print(time.strftime('%X'), 'start', i)
    async with aiohttp.ClientSession() as session:
        async with session.post('http://127.0.0.1:3387/predict', json={'id': i, 'image': image}) as response:
            html = await response.text()
    print(time.strftime('%X'), 'end', i)


async def main():
    for i in range(20):
        task = asyncio.create_task(get(i))
        await task

    tasks = [asyncio.create_task(get(i)) for i in range(20)]
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(main())
