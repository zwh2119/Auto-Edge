ARG dir=audio_classification
FROM python:3.6-slim
MAINTAINER Wenhui Zhou

# Update the package list and install necessary packages
RUN apt-get update && apt-get install -y \
    wget \
    lsb-release \
    software-properties-common \
    gnupg

# Download and run the LLVM installation script
RUN  chmod +x llvm.sh && ./llvm.sh 10

# Set the LLVM_CONFIG environment variable to point to the correct version
ENV LLVM_CONFIG=/usr/bin/llvm-config-10

COPY ./requirements.txt ./

RUN pip3 install --upgrade pip && pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /app
COPY ${dir}/task.py ${dir}/task_queue.py ${dir}/client.py ${dir}/log.py  ${dir}/utils.py ${dir}/config.py ${dir}/audio_classification.py ${dir}/service_server.py /app/

CMD ["python3", "service_server.py"]
