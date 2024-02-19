ARG code_dir=core/generator
ARG lib_dir=core/lib

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

COPY ${lib_dir}/requirements.txt ./lib_requirements.txt
RUN pip install -r lib_requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY ${code_dir}/requirements.txt ./code_requirements.txt
RUN pip install -r code_requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple


COPY ${lib_dir} /home/core/lib
ENV PYTHONPATH "/home/core"

WORKDIR /app
COPY  ${code_dir}/* /app/

CMD ["python3", "main.py"]