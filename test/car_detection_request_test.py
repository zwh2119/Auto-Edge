import asyncio
import aiohttp
import time
import cv2
import requests

import field_codec_utils


async def post(session, data):
    print(time.strftime('%X'), 'start', data['id'])
    async with session.post('http://127.0.0.1:3388/predict', json=data) as response:
        html = await response.text()
    print(time.strftime('%X'), 'end', data['id'], f' result:{html}')


async def task_generator():
    cap = cv2.VideoCapture('traffic-720p.mp4')
    if not cap.isOpened():
        raise Exception('no video found!')
    cnt = 0
    while True:  # 你可以替换为任何持续产生任务的条件
        success, frame = cap.read()
        # frame = cv2.resize(frame, [640, 480])
        # print(frame.shape)
        frame = field_codec_utils.encode_image(frame)
        if not success:
            break
        data = {'id': cnt, 'image': frame}

        yield data  # 假设每个任务都有一个唯一的标识符
        cnt += 1


async def main():
    async with aiohttp.ClientSession() as session:
        tasks = set()
        async for data in task_generator():  # 从生成器中获取新任务
            if len(tasks) >= 20:  # 如果同时运行的任务达到20个，则等待其中一个完成
                _done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            task = asyncio.create_task(post(session, data))
            tasks.add(task)

        # 等待所有剩余的任务完成
        await asyncio.wait(tasks)


if __name__ == '__main__':
    asyncio.run(main())
    # cap = cv2.VideoCapture('traffic-720p.mp4')
    # if not cap.isOpened():
    #     raise Exception('no video found!')
    # cnt = 0
    # while True:  # 你可以替换为任何持续产生任务的条件
    #     success, frame = cap.read()
    #     print(frame.shape)
    #     frame = cv2.resize(frame, [640, 480])
    #     print(frame.shape)
    #     frame = field_codec_utils.encode_image(frame)
    #     if not success:
    #         break
    #     data = {'id': cnt, 'image': frame}
    #     # print(data)
    #     requests.post('http://127.0.0.1:3388/predict', json=data)
    #     break