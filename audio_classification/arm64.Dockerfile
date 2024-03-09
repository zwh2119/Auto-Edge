ARG dir=audio_classification
FROM  dustynv/pytorch:1.10-r32.7.1
MAINTAINER Wenhui Zhou


RUN apt-get update && apt-get install -y \
    wget \
    lsb-release \
    software-properties-common \
    gnupg \
    build-essential  # This will install 'make' and other essential build tools


RUN apt-get update && apt-get install -y llvm  libsndfile1

COPY ./requirements.txt ./

RUN pip3 install --upgrade pip  \
    && pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple


WORKDIR /app
COPY ${dir}/task.py ${dir}/task_queue.py ${dir}/client.py ${dir}/log.py  ${dir}/utils.py ${dir}/config.py ${dir}/audio_classification.py ${dir}/service_server.py /app/

ENV OPENBLAS_CORETYPE=ARMV8

CMD ["python3", "service_server.py"]