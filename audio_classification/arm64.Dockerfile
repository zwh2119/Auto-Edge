ARG dir=audio_classification
FROM  dustynv/pytorch:1.10-r32.7.1
MAINTAINER Wenhui Zhou



# Install essential packages
RUN apt-get update && apt-get install -y \
    wget \
    lsb-release \
    software-properties-common \
    gnupg \
    build-essential \
    libsndfile1

RUN dpkg -i /pdk_files/cuda-repo-l4t-10-2-local_10.2.460-1_arm64.deb
RUN apt-key add /var/cuda-repo*/*.pub \
    && apt-get -y update \
    && apt-get -y install -f cuda-cudart-dev-10-2 \
    && apt-get -y install -f cuda-toolkit-10-2

RUN     dpkg -i /pdk_files/libcudnn8_8.2.1.32-1+cuda10.2_arm64.deb \
     && dpkg -i /pdk_files/libcudnn8-dev_8.2.1.32-1+cuda10.2_arm64.deb \
     && dpkg -i /pdk_files/libcudnn8-samples_8.2.1.32-1+cuda10.2_arm64.deb \
     && dpkg -i /pdk_files/libnvinfer8_8.2.1-1+cuda10.2_arm64.deb  \
     && dpkg -i /pdk_files/libnvinfer-dev_8.2.1-1+cuda10.2_arm64.deb \
     && dpkg -i /pdk_files/libnvparsers8_8.2.1-1+cuda10.2_arm64.deb   \
     && dpkg -i /pdk_files/libnvparsers-dev_8.2.1-1+cuda10.2_arm64.deb \
     && dpkg -i /pdk_files/libnvinfer-plugin8_8.2.1-1+cuda10.2_arm64.deb \
     && dpkg -i /pdk_files/libnvinfer-plugin-dev_8.2.1-1+cuda10.2_arm64.deb \
     && dpkg -i /pdk_files/libnvonnxparsers8_8.2.1-1+cuda10.2_arm64.deb \
     && dpkg -i /pdk_files/libnvonnxparsers-dev_8.2.1-1+cuda10.2_arm64.deb \
     && dpkg -i /pdk_files/libnvinfer-bin_8.2.1-1+cuda10.2_arm64.deb \
     && dpkg -i /pdk_files/libnvinfer-samples_8.2.1-1+cuda10.2_all.deb  \
     && dpkg -i /pdk_files/libnvinfer-doc_8.2.1-1+cuda10.2_all.deb \
     && dpkg -i /pdk_files/graphsurgeon-tf_8.2.1-1+cuda10.2_arm64.deb \
     && dpkg -i /pdk_files/uff-converter-tf_8.2.1-1+cuda10.2_arm64.deb \
     && dpkg -i /pdk_files/python3-libnvinfer_8.2.1-1+cuda10.2_arm64.deb \
     && dpkg -i /pdk_files/python3-libnvinfer-dev_8.2.1-1+cuda10.2_arm64.deb

# Explicitly install a compatible version of LLVM for llvmlite
RUN apt-get install -y llvm-10 llvm-10-dev \
    && update-alternatives --install /usr/bin/llvm-config llvm-config /usr/bin/llvm-config-10 60

COPY ./requirements.txt ./

RUN pip3 install --upgrade pip  \
    && pip3 install --ignore-installed PyYAML -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple


WORKDIR /app
COPY ${dir}/task.py ${dir}/task_queue.py ${dir}/client.py ${dir}/log.py  ${dir}/utils.py ${dir}/config.py ${dir}/audio_classification.py ${dir}/service_server.py /app/

ENV OPENBLAS_CORETYPE=ARMV8

CMD ["python3", "service_server.py"]