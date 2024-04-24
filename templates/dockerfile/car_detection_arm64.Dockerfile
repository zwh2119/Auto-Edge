ARG base_dir=core/processor
ARG lib_dir=core/lib
ARG code_dir=applications/road_surveillance/car_detection

FROM  onecheck/tensorrt:trt8_aarch64
MAINTAINER Wenhui Zhou

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN pip3 install --upgrade pip
RUN pip3 install --upgrade pip
COPY ${lib_dir}/requirements.txt ./lib_requirements.txt
RUN pip install -r lib_requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY ${base_dir}/requirements.txt ./base_requirements.txt
RUN pip install -r base_requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY ${code_dir}/requirements_arm64.txt ./code_requirements.txt
RUN pip install -r code_requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple


WORKDIR /app
COPY ${dir}/car_detection_trt.py ${dir}/service_server.py ${dir}/log.py ${dir}/config.py  /app/

CMD ["uvicorn", "service_server:app", "--host=0.0.0.0", "--port=9001", "--log-level=debug", "--workers=2", "--limit-concurrency=3"]
