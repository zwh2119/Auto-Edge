## new in middle branch
- support multi data stream of different modal
- support task queue of multi priority
- support task type of periodic tasks and abrupt tasks

# Auto-Edge

<center>
    <img src="pic/logo.png" alt="logo" width="120">
</center>

## Brief Introduction


Auto-Edge is an automated scheduling platform for edge computing. it's developed based on KubeEdge.


## Architecture
![](pic/structure.png)

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
more args of docker building script can be found with `--help`

up-to-date images has been built on [dockerhub](https://hub.docker.com/u/onecheck).


### deploy necessary files on cloud and edge
Some customized files needed to be deployed on devices previously and corresponding paths need to be filled in yaml files.

file structure:
```
cloud device:
- {code_dir}/files
  - schedule_config.yaml
- {code_dir}/model_lib
  - libmyplugins.so
  - yolov5s.engine

edge device:
- {code_dir}/files
  - video_config.yaml
- {code_dir}/model_lib
  - libmyplugins.so
  - yolov5s.engine
```
The 'model_lib' folder contains files for service inference, and it differs among different services.(current is for car-detection).

The template deploying files can be found in [shared link](https://box.nju.edu.cn/d/1c26b20dc733474c9a6b/)

### delete former pods of Auto-Edge
```shell
bash docker/delete.sh
```

### start Auto-Edge system on KubeEdge
start system with yaml files (eg:[video_car_detection.yaml](templates/video_car_detection.yaml))
```shell
# yaml files can be found in `templates` folder
kubectl apply -f <file-name>
```

find pods of system, default namespace is  `auto-edge`.
```shell
kubectl get pods -n <namespace-name>
```

query the log of pods.
```shell
kubectl logs <pod-name>
```

describe resource for pods.
```shell
kubectl describe pod <pod-name>

```

### start rtsp video stream
```shell
# multiple video stream binding to different edge
ffmpeg -re -i ./traffic0.mp4 -vcodec libx264 -f rtsp rtsp://127.0.0.1/video0
ffmpeg -re -i ./traffic1.mp4 -vcodec libx264 -f rtsp rtsp://127.0.0.1/video1
ffmpeg -re -i ./traffic2.mp4 -vcodec libx264 -f rtsp rtsp://127.0.0.1/video2
```

### collect result from Auto-Edge
```shell
python tools/result_collector.py
```

or you can mount the data record folder in distributor to volume on physical device

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
- [sedna](https://github.com/AdaYangOlzz/sedna-modified)

## Deployment Device
- Cloud: NVIDIA GeForce RTX 3090 *4
- Edge: NVIDIA Jetson TX2

## Supported Service Pipeline
- `Car Detection`: [detection]
- `Class Detection`: [face detection, pose estimation] (not completely support now)

## Development Version
- 2023.11.25 `AutoEdge` - `v0.1.0`: demo of car detection (without scheduler) test successfully [single edge, single stage].
- 2023.11.30 `AutoEdge` - `v0.2.0`: demo of car detection (with scheduler) test successfully [single edge, single stage].
- 2023.12.02 `AutoEdge` - `v0.3.0`: build docker image of all components for car detection demo.
- 2023.12.04 `AutoEdge` - `v0.4.0`: demo of classroom detection (with scheduler) test successfully [single edge, multi stage].
- 2023.12.11 `AutoEdge` - `v0.5.0`: service of car detection has been transformed by TensorRT.
- 2023.12.11 `AutoEdge` - `v0.6.0`: demo of car detection successfully test on multi-edge [multi edge, single stage].
- 2023.12.13 `AutoEdge` - `v0.7.0`: add logger and collapse processing.
- 2023.12.17 `AutoEdge` - `v0.8.0`: add resource monitor component.
- 2024.01.06 `AutoEdge` - `v0.9.0`: build docker images of all components. 
- 2024.01.11 `AutoEdge` - `v1.0.0`: complete the first formal version of Auto-Edge.
- 2024.01.14 `AutoEdge` - `mid-v0.1.0`: complete supporting multi-priority task queue.

## Citation
