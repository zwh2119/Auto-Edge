ARG code_dir=core/controller
ARG lib_dir=core/lib

FROM python:3.6
MAINTAINER Wenhui Zhou

COPY ${lib_dir}/requirements.txt ./lib_requirements.txt
RUN pip install -r lib_requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY ${code_dir}/requirements.txt ./code_requirements.txt
RUN pip install -r code_requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple


COPY ${lib_dir} /home/core/lib
ENV PYTHONPATH "/home/core"

WORKDIR /app
COPY  ${code_dir}/* /app/


CMD ["gunicorn", "main:app", "-c", "./gunicorn.conf.py"]