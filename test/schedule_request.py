import asyncio
import time

import aiohttp

async def post(session, data):
    # print(time.strftime('%X'), 'start', data['id'])
    async with session.get('http://127.0.0.1:8175/schedule',json={'source_id':1}) as response:
        html = await response.text()
    print(time.strftime('%X'), f' result:{html}')

async def task_generator():

    cnt = 0
    while True:  # 你可以替换为任何持续产生任务的条件
        data = cnt
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
