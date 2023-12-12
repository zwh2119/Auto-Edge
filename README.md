# Auto-Edge

<center>
    <img src="pic/logo.png" alt="logo" width="120">
</center>

## Brief Introduction


Auto-Edge is an automated scheduling platform for edge computing. it's developed based on KubeEdge.


## Quick Start
### python start 
(**for debug only**)

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

docker build -t "component_name:temp" -f ./Dockerfile .

docker login --username=onecheck registry.cn-hangzhou.aliyuncs.com

# on cloud (x86/amd version)
docker tag 195049bfcbcb registry.cn-hangzhou.aliyuncs.com/auto-edge/distributor:temp
docker push registry.cn-hangzhou.aliyuncs.com/auto-edge/distributor:temp

docker tag ee31d2e73705 registry.cn-hangzhou.aliyuncs.com/auto-edge/scheduler:temp
docker push registry.cn-hangzhou.aliyuncs.com/auto-edge/scheduler:temp

docker tag 03d66074b68b registry.cn-hangzhou.aliyuncs.com/auto-edge/controller:temp
docker push registry.cn-hangzhou.aliyuncs.com/auto-edge/controller:temp

docker tag 69d23d4631de registry.cn-hangzhou.aliyuncs.com/auto-edge/car-detection-service:temp
docker push registry.cn-hangzhou.aliyuncs.com/auto-edge/car-detection-service:temp

# on edge (arm version)
docker tag 30e10b53b69e registry.cn-hangzhou.aliyuncs.com/auto-edge/generator-arm:temp
docker push registry.cn-hangzhou.aliyuncs.com/auto-edge/generator-arm:temp

docker tag d1a8fa82decd registry.cn-hangzhou.aliyuncs.com/auto-edge/controller-arm:temp
docker push registry.cn-hangzhou.aliyuncs.com/auto-edge/controller-arm:temp

docker tag 01890da27d39 registry.cn-hangzhou.aliyuncs.com/auto-edge/car-detection-service-arm:temp
docker push registry.cn-hangzhou.aliyuncs.com/auto-edge/car-detection-service-arm:temp


```

### KubeEdge start 
(**recommend**)
```shell

```

## Related Framework
- [docker container](https://github.com/docker/docker-ce)
- [Kubernetes](https://github.com/kubernetes/kubernetes)
- [KubeEdge](https://github.com/kubeedge/kubeedge)
- [Sedna](https://github.com/kubeedge/sedna)
- [TensorRT](https://developer.nvidia.com/tensorrt)

## Components
- [data generator](https://github.com/zwh2119/data-generator)
- [data distributor](https://github.com/zwh2119/data-distributor)
- data aggregator (**deprecated**)
- [service processor](https://github.com/zwh2119/car-detection)
- [scheduler](https://github.com/zwh2119/application-scheduler)
- [edge controller](https://github.com/zwh2119/edge-controller) (**use as controller**)
- cloud controller (**deprecated**)
- [resource monitor](https://github.com/zwh2119/resource-monitor)

## Reference Deployment Device

## Development Version
- 2023.11.25 AutoEdge - v0.1.0: demo of car detection (without scheduler) test successfully [single edge, single stage]
- 2023.11.30 AutoEdge - v0.2.0: demo of car detection (with scheduler) test successfully [single edge, single stage]
- 2023.12.02 AutoEdge - v0.3.0: build docker image of all components for car detection demo
- 2023.12.04 AutoEdge - v0.4.0: demo of classroom detection (with scheduler) test successfully [single edge, multi stage]
- 2023.12.11 AutoEdge - v0.5.0: service of car detection has been transformed by TensorRT 
- 2023.12.11 AutoEdge - v0.6.0: demo of car detection successfully test on multi-edge [multi edge, single stage]


## Citing
