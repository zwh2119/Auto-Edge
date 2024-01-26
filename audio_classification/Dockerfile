ARG dir=audio_classification
FROM python:3.8-slim
MAINTAINER Wenhui Zhou

RUN apt-get update && apt-get install -y gnupg wget software-properties-common
RUN wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key | apt-key add - 15CF4D18AF4F7421
RUN apt-add-repository "deb http://apt.llvm.org/stretch/ llvm-toolchain-stretch-6.0 main"
RUN apt-get update
RUN apt-get -y install cython python-llvm build-essential libedit-dev
RUN apt-get -y install libllvm6.0 llvm-6.0-dev llvm-dev

COPY ./requirements.txt ./

RUN pip3 install --upgrade pip && pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /app
COPY ${dir}/task.py ${dir}/task_queue.py ${dir}/client.py ${dir}/log.py  ${dir}/utils.py ${dir}/config.py ${dir}/audio_classification.py ${dir}/service_server.py /app/

CMD ["python3", "service_server.py"]
