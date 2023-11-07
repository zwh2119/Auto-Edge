import time
import contextlib
import threading
import asyncio

from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.responses import JSONResponse
from starlette.requests import Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from gunicorn.app.base import BaseApplication


class StandaloneApplication(BaseApplication):

    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {key: value for key, value in self.options.items()
                  if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


class Server(uvicorn.Server):
    def install_signal_handlers(self):
        pass

    @contextlib.contextmanager
    def run_in_thread(self):
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        try:
            yield thread
        finally:
            self.should_exit = True
            thread.join()


class BaseServer:

    DEBUG = True
    WAIT_TIME = 15

    def __init__(self):
        self.app = FastAPI(routes=[
            APIRoute('/test',
                     self.test_func,
                     response_class=JSONResponse,
                     methods=['GET']

                     ),
        ], log_level='trace', timeout=600)

    def run(self, **kwargs):
        app = self.app
        if hasattr(app, "add_middleware"):
            print('add middleware')
            app.add_middleware(
                CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                allow_methods=["*"], allow_headers=["*"],
            )

        # config = uvicorn.Config(
        #     app,
        #     host='127.0.0.1',
        #     port=3387,
        #     workers=10,
        #     timeout_keep_alive=300,
        #     log_level="info",
        #     **kwargs)
        # server = Server(config=config)
        # with server.run_in_thread() as current_thread:
        #     return self.wait_stop(current=current_thread)

        options = {
            'bind': '0.0.0.0:3387',
            'workers': 10,
            'worker_class': 'uvicorn.workers.UvicornWorker',
            'timeout': 6000,
        }
        StandaloneApplication(app, options).run()

    async def large_time_func(self):
        print(time.strftime('%X'), 'start')
        cnt = 0
        for i in range(100000000):
            cnt += i
        print(time.strftime('%X'), 'end')
    async def test_func(self, request: Request):
        data = await request.json()
        await self.large_time_func()
        print(data['number'])
        return {'data':1}

    def wait_stop(self, current):
        """wait the stop flag to shutdown the server"""
        while 1:
            time.sleep(self.WAIT_TIME)
            if not current.is_alive():
                return
            if getattr(self.app, "shutdown", False):
                return


if __name__ == '__main__':
    app_server = BaseServer()
    app_server.run()
