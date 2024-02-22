import os
import time

import uvicorn
from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form, Body, Request

from fastapi.routing import APIRoute
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from kubernetes import client, config
import requests

app = FastAPI()


@app.get("/serv/get_service_list")
async def get_service_list():
    pass


@app.get("/serv/get_execute_url/{service}")
async def get_service_info(service):
    pass


@app.post("/serv/update-dag-workflows-api")
async def update_pipeline():
    pass


@app.get("/dag/node/get_video_info")
async def get_video_info():
    pass


@app.get("/serv/get-dag-workflows-api")
def get_pipeline():
    pass


@app.post("/dag/query/submit_query")
def submit_task():
    pass


def main():
    uvicorn.run(app, host='0.0.0.0', port=8910)


if __name__ == '__main__':
    main()
