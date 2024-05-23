FROM onecheck/opencv:latest

MAINTAINER Wenhui Zhou

ARG dependency_dir=dependency
ARG lib_dir=dependency/core/lib
ARG base_dir=dependency/core/generator
ARG code_dir=components/generator

# Required to build Ubuntu 20.04 without user prompts with DLFW container
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y tzdata

ENV TZ=Asia/Shanghai

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone

# Install python3
RUN apt-get install -y --no-install-recommends \
      python3 \
      python3-pip \
      python3-dev \
      python3-wheel &&\
    cd /usr/local/bin &&\
    ln -s /usr/bin/python3 python &&\
    ln -s /usr/bin/pip3 pip;

COPY ${lib_dir}/requirements.txt ./lib_requirements.txt
COPY ${base_dir}/requirements.txt ./base_requirements.txt

RUN pip install --upgrade pip setuptools wheel && \
    pip install -r lib_requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install -r base_requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple



COPY ${dependency_dir} /home/dependency
ENV PYTHONPATH "/home/dependency"

WORKDIR /app
COPY  ${code_dir}/* /app/

CMD ["python3", "main.py"]