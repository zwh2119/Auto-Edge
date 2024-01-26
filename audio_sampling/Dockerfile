ARG dir=audio_sampling
FROM python:3.6
MAINTAINER Wenhui Zhou

RUN apt-get update && apt-get install llvm-8

COPY ./requirements.txt ./
RUN pip3 install --upgrade pip && pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /app
COPY ${dir}/task.py ${dir}/task_queue.py ${dir}/client.py ${dir}/log.py  ${dir}/utils.py ${dir}/config.py ${dir}/audio_sampling.py ${dir}/service_server.py /app/

CMD ["python3", "service_server.py"]
