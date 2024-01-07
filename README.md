# Auto-Edge

<center>
    <img src="pic/logo.png" alt="logo" width="120">
</center>

## Brief Introduction


Auto-Edge is an automated scheduling platform for edge computing. it's developed based on KubeEdge.


## Quick Start

there are three ways to start Auto-Edge system: python start (start from python source code), docker start (start from compiled docker), KubEdge start (start with KubeEdge system deployment).

### Python start 
(**for debug only, already been deprecated!**)

### Docker start
#### docker build
1. install docker buildx on x86 platform ([instruction](instructions/buildx.md))
2. build docker with script
```shell
bash docker/build.sh
```
more args of docker building script can be found with --help 

#### docker run
```shell
### or docker can be deployed with docker-compose (in 'docker' folder)
# cloud
docker run onecheck/controller:{tag} -p 9200
docker run onecheck/distributor:{tag} -p 9500
docker run onecheck/scheduler:{tag} -p 9400
docker run onecheck/monitor:{tag}
docker run --gpus all -v {code_dir}/car_detection/lib:/app/lib -p 9001  onecheck/car-detection:{tag}

#edge
docker run onecheck/controller:{tag} -p 9200
docker run onecheck/monitor:{tag}
docker run onecheck/generator:{tag}
docker run --gpus all -v {code_dir}/car_detection/lib:/app/lib -p 9001  onecheck/car-detection:{tag}


```

### KubeEdge start 
(**recommend**)
```shell
### yaml files can be found in 'templates' folder

```

### RTSP video 
```shell
# video rtsp
ffmpeg -re -i ./traffic0.mp4 -vcodec libx264 -f rtsp rtsp://127.0.0.1/video0

ffmpeg -re -i ./traffic1.mp4 -vcodec libx264 -f rtsp rtsp://127.0.0.1/video1

ffmpeg -re -i ./traffic2.mp4 -vcodec libx264 -f rtsp rtsp://127.0.0.1/video2
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

## Deployment Device
- Cloud: NVIDIA GeForce RTX 3090 *4
- Edge: NVIDIA Jetson TX2

## Development Version
- 2023.11.25 AutoEdge - v0.1.0: demo of car detection (without scheduler) test successfully [single edge, single stage]
- 2023.11.30 AutoEdge - v0.2.0: demo of car detection (with scheduler) test successfully [single edge, single stage]
- 2023.12.02 AutoEdge - v0.3.0: build docker image of all components for car detection demo
- 2023.12.04 AutoEdge - v0.4.0: demo of classroom detection (with scheduler) test successfully [single edge, multi stage]
- 2023.12.11 AutoEdge - v0.5.0: service of car detection has been transformed by TensorRT 
- 2023.12.11 AutoEdge - v0.6.0: demo of car detection successfully test on multi-edge [multi edge, single stage]
- 2023.12.13 AutoEdge - v0.7.0: add logger and collapse processing
- 2023.12.17 AutoEdge - v0.8.0: add resource monitor component 
- 2024.01.06 AutoEdge - v0.9.0: build docker images of all components 


## Citation
