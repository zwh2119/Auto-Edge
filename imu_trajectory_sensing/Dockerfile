ARG dir=imu_trajectory_sensing
FROM python:3.6
MAINTAINER Wenhui Zhou


COPY ./requirements.txt ./
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /app
COPY ${dir}/task.py ${dir}/task_queue.py ${dir}/client.py ${dir}/log.py  ${dir}/utils.py ${dir}/config.py ${dir}/imu_trajectory_sensing.py ${dir}/service_server.py /app/

CMD ["OPENBLAS_CORETYPE=ARMV8","python3", "service_server.py"]

