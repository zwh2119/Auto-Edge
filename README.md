# Auto-Edge

<center>
    <img src="pic/logo.png" alt="logo" width="120">
</center>

## Brief Introduction


Auto-Edge is an automated scheduling platform for edge computing. it's developed based on KubeEdge.


## Features

Auto-Edge has the following features:

## Architecture


## Guides

### build environment on cloud and edge devices
1. deploy Kubernetes on cloud device
2. deploy KubeEdge on cloud and edge devices
3. deploy Sedna (modified version) on cloud and edge devices

### build docker images of Auto-Edge components
1. install docker buildx on x86 platform ([instruction](instructions/buildx.md))
2. build docker with script
```shell
bash docker/build.sh
```
more args of docker building script can be found with --help 

up-to-date images has been built on [dockerhub](https://hub.docker.com/u/onecheck).


### start Auto-Edge system on KubeEdge
```shell
### yaml files can be found in 'templates' folder
kubectl apply -f <file-name>

kubectl get pods -n <namespace-name>

kubectl logs <pod-name>

kubectl describe pod <pod-name>

```

### start rtsp video stream
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
- [generator](https://github.com/zwh2119/data-generator)
- [distributor](https://github.com/zwh2119/data-distributor)
- [service processor](https://github.com/zwh2119/car-detection)
- [scheduler](https://github.com/zwh2119/application-scheduler)
- [controller](https://github.com/zwh2119/edge-controller)
- [monitor](https://github.com/zwh2119/resource-monitor)

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
