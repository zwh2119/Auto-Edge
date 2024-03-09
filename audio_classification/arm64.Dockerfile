ARG dir=audio_classification
FROM  dustynv/pytorch:1.10-r32.7.1
MAINTAINER Wenhui Zhou


# Install essential packages
RUN apt-get update && apt-get install -y \
    wget \
    lsb-release \
    software-properties-common \
    gnupg \
    build-essential \
    libsndfile1

# Explicitly install a compatible version of LLVM for llvmlite
RUN apt-get install -y llvm-10 llvm-10-dev \
    && update-alternatives --install /usr/bin/llvm-config llvm-config /usr/bin/llvm-config-10 60

COPY ./requirements.txt ./

RUN pip3 install --upgrade pip  \
    && pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple


WORKDIR /app
COPY ${dir}/task.py ${dir}/task_queue.py ${dir}/client.py ${dir}/log.py  ${dir}/utils.py ${dir}/config.py ${dir}/audio_classification.py ${dir}/service_server.py /app/

ENV OPENBLAS_CORETYPE=ARMV8

CMD ["python3", "service_server.py"]