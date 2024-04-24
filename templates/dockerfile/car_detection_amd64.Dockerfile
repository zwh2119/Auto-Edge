ARG base_dir=core/processor
ARG lib_dir=core/lib
ARG code_dir=applications/road_surveillance/car_detection

FROM yuefan2022/tensorrt-ubuntu20.04-cuda11.6
MAINTAINER Wenhui Zhou

RUN pip3 install --upgrade pip
COPY ${lib_dir}/requirements.txt ./lib_requirements.txt
RUN pip install -r lib_requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY ${base_dir}/requirements.txt ./base_requirements.txt
RUN pip install -r base_requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY ${code_dir}/requirements_amd64.txt ./code_requirements.txt
RUN pip install -r code_requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY ${lib_dir} /home/core/lib
COPY ${base_dir} /home/core/processor
ENV PYTHONPATH "/home/core"

WORKDIR /app
COPY  ${code_dir}/* /app/


CMD ["uvicorn", "service_server:app", "--host=0.0.0.0", "--port=9001", "--log-level=debug", "--workers=2", "--limit-concurrency=3"]
