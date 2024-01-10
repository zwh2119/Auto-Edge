ARG dir=data-distributor

FROM python:3.6
MAINTAINER Wenhui Zhou

COPY ./requirements.txt ./
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /app
COPY  ${dir}/client.py ${dir}/distributor_server.py ${dir}/gunicorn.conf.py ${dir}/log.py ${dir}/utils.py ${dir}/config.py /app/

CMD ["gunicorn", "distributor_server:app", "-c", "./gunicorn.conf.py"]