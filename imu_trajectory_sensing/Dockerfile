ARG dir=car_detection
FROM yuefan2022/tensorrt-ubuntu20.04-cuda11.6
MAINTAINER Wenhui Zhou

RUN pip3 install --upgrade pip \
    && pip install typing_extensions==4.8.0 -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && pip install opencv-python-headless -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && pip install PyYAML --ignore-installed -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY ./requirements.txt ./
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /app
COPY ${dir}/car_detection_trt.py ${dir}/service_server.py ${dir}/log.py ${dir}/config.py ${dir}/client.py ${dir}/utils.py ${dir}/task.py ${dir}/task_queue.py  /app/


CMD ["python", "service_server.py"]
