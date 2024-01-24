ARG dir=generator

FROM gocv/opencv:latest

MAINTAINER Wenhui Zhou

# Required to build Ubuntu 20.04 without user prompts with DLFW container
ENV DEBIAN_FRONTEND=noninteractive


# Install python3
RUN apt-get install -y --no-install-recommends \
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
COPY  ${dir}/generator_server.py ${dir}/log.py ${dir}/client.py  ${dir}/video_generator.py ${dir}/audio_generator.py ${dir}/imu_generator.py ${dir}/yaml_utils.py ${dir}/utils.py ${dir}/config.py /app/

CMD ["python3", "generator_server.py"]