FROM --platform=linux/amd64 onecheck/tensorrt:trt8_amd64
MAINTAINER Wenhui Zhou

ARG dependency_dir=dependency
ARG lib_dir=dependency/core/lib
ARG base_dir=dependency/core/processor
ARG code_dir=components/processor
ARG app_dir=dependency/core/applications/road_surveillance/car_detection


RUN pip3 install --upgrade pip
COPY ${lib_dir}/requirements.txt ./lib_requirements.txt
RUN pip install -r lib_requirements.txt --ignore-installed -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY ${base_dir}/requirements.txt ./base_requirements.txt
RUN pip install -r base_requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY ${app_dir}/requirements_amd64.txt ./app_requirements.txt
RUN pip install -r app_requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY ${dependency_dir} /home/dependency
ENV PYTHONPATH "/home/dependency"

WORKDIR /app
COPY  ${code_dir}/* /app/


CMD ["python3", "main.py"]

FROM --platform=linux/arm64 onecheck/tensorrt:trt8_aarch64
MAINTAINER Wenhui Zhou

ARG dependency_dir=dependency
ARG lib_dir=dependency/core/lib
ARG base_dir=dependency/core/processor
ARG code_dir=components/processor
ARG app_dir=dependency/core/applications/road_surveillance/car_detection


ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN pip3 install --upgrade pip

COPY ${lib_dir}/requirements.txt ./lib_requirements.txt
RUN pip install -r lib_requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY ${base_dir}/requirements.txt ./base_requirements.txt
RUN pip install -r base_requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY ${app_dir}/requirements_arm64.txt ./app_requirements.txt
RUN pip install -r app_requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple


COPY ${dependency_dir} /home/dependency
ENV PYTHONPATH "/home/dependency"

WORKDIR /app
COPY  ${code_dir}/* /app/

CMD ["python3", "main.py"]


