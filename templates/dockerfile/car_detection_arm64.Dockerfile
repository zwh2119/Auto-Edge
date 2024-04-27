ARG dependency_dir=dependency
ARG lib_dir=dependency/core/lib
ARG base_dir=dependency/core/processor
ARG code_dir=components/processor
ARG app_dir=dependency/core/applications/road_surveillance/cardetection

FROM  onecheck/tensorrt:trt8_aarch64
MAINTAINER Wenhui Zhou

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN pip3 install --upgrade pip

COPY ${lib_dir}/requirements.txt ./lib_requirements.txt
RUN pip install -r lib_requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY ${base_dir}/requirements.txt ./base_requirements.txt
RUN pip install -r base_requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY ${app_dir}requirements_arm64.txt ./app_requirements.txt
RUN pip install -r app_requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple


COPY ${dependency_dir} /home/dependency
ENV PYTHONPATH "/home/dependency"

WORKDIR /app
COPY  ${code_dir}/* /app/

CMD ["uvicorn", "service_server:app", "--host=0.0.0.0", "--port=9001", "--log-level=debug", "--workers=2", "--limit-concurrency=3"]
