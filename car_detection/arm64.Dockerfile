ARG dir=car_detection
FROM  onecheck/tensorrt:trt8_aarch64
MAINTAINER Wenhui Zhou

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN pip3 install --upgrade pip

COPY ./requirements.txt ./
RUN pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /app
COPY ${dir}/car_detection_trt.py ${dir}/service_server.py ${dir}/log.py ${dir}/config.py ${dir}/client.py ${dir}/utils.py ${dir}/task.py ${dir}/task_queue.py   /app/

CMD ["python3", "service_server.py"]

