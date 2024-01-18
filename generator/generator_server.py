import yaml_utils
import threading
from video_generator import VideoGenerator
from utils import *
from client import http_request

from config import Context


def main():
    scheduler_path = 'schedule'
    scheduler_port = Context.get_parameters('scheduler_port')
    controller_port = Context.get_parameters('controller_port')
    scheduler_ip = get_nodes_info()[Context.get_parameters('scheduler_name')]

    video_config = yaml_utils.read_yaml(Context.get_file_path('video_config.yaml'))
    videos = video_config['video']
    http_request(url=get_merge_address(scheduler_ip, port=scheduler_port, path='config'),
                 method='POST', json=videos)

    scheduler_address = get_merge_address(scheduler_ip, port=scheduler_port, path=scheduler_path)
    task_manage_address = get_merge_address(scheduler_ip, port=scheduler_port, path='task')
    for video in videos:
        video_generator = VideoGenerator(video['url'], video['id'], video['priority'],
                                         scheduler_address, task_manage_address,
                                         controller_port, video['resolution'],
                                         video['fps'])
        threading.Thread(target=video_generator.run).start()


if __name__ == '__main__':
    main()
