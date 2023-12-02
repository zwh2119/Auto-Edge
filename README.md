# Auto-Edge: an Auto Scheduling Platform for Edge Computing based on KubeEdge



## Brief Introduction
<center>
    <img src="pic/logo.png" alt="logo" width="120">
</center>

Auto-Edge is an automated scheduling platform for edge computing. it's developed based on KubeEdge.


## Quick Start
### python start 
(**for debug only**)

(**will be deprecated in the late version**)

```shell

# cloud
gunicorn controller_server:app -w 4 -k uvicorn.workers.UvicornWorker --log-level debug --bind 0.0.0.0:9002


gunicorn distributor_server:app -w 1 -k uvicorn.workers.UvicornWorker --log-level debug --bind 0.0.0.0:5713


gunicorn service_server:app -w 4 -k uvicorn.workers.UvicornWorker --log-level debug --bind 0.0.0.0:9001


# edge
python3 generator_server.py

gunicorn controller_server:app -w 2 -k uvicorn.workers.UvicornWorker --log-level debug --bind 0.0.0.0:9002


gunicorn service_server:app -w 1 -k uvicorn.workers.UvicornWorker --log-level debug --bind 0.0.0.0:9001 --timeout 60


# video rtsp
ffmpeg -re -i ./traffic0.mp4 -vcodec libx264 -f rtsp rtsp://127.0.0.1/video0

ffmpeg -re -i ./traffic1.mp4 -vcodec libx264 -f rtsp rtsp://127.0.0.1/video1

ffmpeg -re -i ./traffic2.mp4 -vcodec libx264 -f rtsp rtsp://127.0.0.1/video2
```

### docker start
```shell

cd component_name
# x86/amd version for cloud
docker build -t "component_name:temp" -f ./Dockerfile .

docker login --username=onecheck registry.cn-hangzhou.aliyuncs.com

docker tag 195049bfcbcb registry.cn-hangzhou.aliyuncs.com/auto-edge/distributor:temp
docker push registry.cn-hangzhou.aliyuncs.com/auto-edge/distributor:temp

docker tag ee31d2e73705 registry.cn-hangzhou.aliyuncs.com/auto-edge/scheduler:temp
docker push registry.cn-hangzhou.aliyuncs.com/auto-edge/scheduler:temp

docker tag 03d66074b68b registry.cn-hangzhou.aliyuncs.com/auto-edge/controller:temp
docker push registry.cn-hangzhou.aliyuncs.com/auto-edge/controller:temp

docker tag 30e10b53b69e registry.cn-hangzhou.aliyuncs.com/auto-edge/generator-arm:temp
docker push registry.cn-hangzhou.aliyuncs.com/auto-edge/generator-arm:temp

docker tag d1a8fa82decd registry.cn-hangzhou.aliyuncs.com/auto-edge/controller-arm:temp
docker push registry.cn-hangzhou.aliyuncs.com/auto-edge/controller-arm:temp


# arm version for edge
```

### KubeEdge start 
(**recommend**)
```shell

```

## Related Framework
- docker container
- Kubernetes
- KubeEdge
- Sedna

## Components
- data generator
- data distributor
- data aggregator (**deprecated**)
- service processor
- scheduler
- edge controller (**use as controller**)
- cloud controller (**deprecated**)

## Development Version
- 2023.11.25 AutoEdge - v0.1.0: demo of car detection (without scheduler) test successfully
- 2023.11.30 AutoEdge - v0.2.0: demo of car detection (with scheduler) test successfully
- 2023.12.02 AutoEdge - v0.3.0: build docker image of all components for car detection demo


## Citing
