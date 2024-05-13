workers = 1    # 定义同时开启的处理请求的进程数量，根据网站流量适当调整

worker_class = "uvicorn.workers.UvicornWorker"   # 采用gevent库，支持异步处理请求，提高吞吐量

bind = "0.0.0.0:9400"

accesslog = '-'

errorlog = '-'
