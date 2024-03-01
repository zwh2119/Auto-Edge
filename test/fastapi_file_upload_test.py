import json
import os

from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form

from fastapi.routing import APIRoute
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

class ControllerServer:
    def __init__(self):
        self.app = FastAPI(routes=[
            APIRoute('/test_upload',
                     self.deal_response,
                     response_class=JSONResponse,
                     methods=['POST']
                     ),
        ], log_level='trace', timeout=6000)

        self.app.add_middleware(
            CORSMiddleware, allow_origins=["*"], allow_credentials=True,
            allow_methods=["*"], allow_headers=["*"],
        )

    async def deal_response(self,  file: UploadFile = File(...), data: str = Form(...)):
        file_data = await file.read()
        print(len(file_data))
        print(json.loads(data))
        return {'msg': 'data send success!'}


if __name__ == '__main__':
    server = ControllerServer()
    uvicorn.run(server.app, host='0.0.0.0', port=1234)
