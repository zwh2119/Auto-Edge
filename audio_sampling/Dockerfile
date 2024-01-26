ARG dir=audio_sampling
FROM python:3.8-slim
MAINTAINER Wenhui Zhou

RUN wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key | sudo apt-key add -

RUN apt-add-repository "deb http://apt.llvm.org/xenial/ llvm-toolchain-xenial-8 main"
RUN apt-add-repository "deb-src http://apt.llvm.org/xenial/ llvm-toolchain-xenial-8 main"

RUN apt-get update && apt-get install -y --no-install-recommends libedit-dev build-essential \
    && apt-get install -y --no-install-recommends  llvm-8 llvm-8-dev

RUN LLVM_CONFIG=/usr/bin/llvm-config-8 pip3 install enum34 llvmlite numba


COPY ./requirements.txt ./
RUN pip3 install --upgrade pip && pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /app
COPY ${dir}/task.py ${dir}/task_queue.py ${dir}/client.py ${dir}/log.py  ${dir}/utils.py ${dir}/config.py ${dir}/audio_sampling.py ${dir}/service_server.py /app/

CMD ["python3", "service_server.py"]
