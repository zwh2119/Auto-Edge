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
