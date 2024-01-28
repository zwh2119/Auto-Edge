ARG dir=edge_edye/stage2

FROM gocv/opencv:latest

MAINTAINER Wenhui Zhou

ENV DEBIAN_FRONTEND=noninteractive

# Install python3
RUN apt-get -y update && apt-get install -y --no-install-recommends \
      python3 \
      python3-pip \
      python3-dev \
      python3-wheel &&\
    cd /usr/local/bin &&\
    ln -s /usr/bin/python3 python &&\
    ln -s /usr/bin/pip3 pip;

RUN pip install --upgrade pip setuptools wheel

COPY ./requirements.txt ./
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /app
COPY   ${dir}/*  /app/

CMD ["python3", "service_server.py"]