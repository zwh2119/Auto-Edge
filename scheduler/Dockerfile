ARG dir=app_schedule

FROM python:3.8
MAINTAINER Wenhui Zhou

COPY ./requirements.txt ./
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /app
COPY ${dir}/schedule_server.py ${dir}/task_schedule.py ${dir}/priority_schedule.py ${dir}/pid.py ${dir}/log.py ${dir}/utils.py ${dir}/gunicorn.conf.py ${dir}/yaml_utils.py ${dir}/config.py  /app/


CMD ["gunicorn", "schedule_server:app", "-c", "./gunicorn.conf.py"]