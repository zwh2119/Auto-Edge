FROM dockerhub.ifan.dev/pytorch/pytorch:2.0.0-cuda11.7-cudnn8-devel

LABEL authors="Wenhui Zhou"

ARG dependency_dir=dependency
ARG lib_dir=dependency/core/lib
ARG base_dir=dependency/core/scheduler
ARG code_dir=components/scheduler

ENV DEBIAN_FRONTEND=noninteractive

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
ENV PYTHONPATH="/home/dependency"

WORKDIR /app
COPY  ${code_dir}/* /app/


CMD ["gunicorn", "main:app", "-c", "./gunicorn.conf.py"]
