FROM python:3.6
MAINTAINER Wenhui Zhou

ARG dependency_dir=dependency
ARG lib_dir=dependency/core/lib
ARG base_dir=dependency/core/controller
ARG code_dir=components/controller

RUN apt-get update && \
    apt-get install -y tzdata

ENV TZ=Asia/Shanghai

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone

COPY ${lib_dir}/requirements.txt ./lib_requirements.txt
COPY ${base_dir}/requirements.txt ./base_requirements.txt

RUN pip3 install --upgrade pip && \
    pip install -r lib_requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install -r base_requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple


COPY ${dependency_dir} /home/dependency
ENV PYTHONPATH "/home/dependency"

WORKDIR /app
COPY  ${code_dir}/* /app/


CMD ["gunicorn", "main:app", "-c", "./gunicorn.conf.py"]
