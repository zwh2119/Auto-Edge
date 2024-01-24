import yaml_utils
import threading
from video_generator import VideoGenerator
from imu_generator import IMUGenerator
from audio_generator import AudioGenerator

from utils import *
from client import http_request

from config import Context


def main():
    scheduler_path = 'schedule'
    data_modal = Context.get_parameters('modal')
    config_file = '{}_config.yaml'.format(data_modal)
    scheduler_port = Context.get_parameters('scheduler_port')
    controller_port = Context.get_parameters('controller_port')
    scheduler_ip = get_nodes_info()[Context.get_parameters('scheduler_name')]

    data_config = yaml_utils.read_yaml(Context.get_file_path(config_file))
    data = data_config[data_modal]
    response = None
    while not response:
        response = http_request(url=get_merge_address(scheduler_ip, port=scheduler_port, path='config'),
                                method='POST', json={'config': data})

    scheduler_address = get_merge_address(scheduler_ip, port=scheduler_port, path=scheduler_path)
    task_manage_address = get_merge_address(scheduler_ip, port=scheduler_port, path='task')
    for source in data:
        generator = None
        if data_modal == 'video':
            generator = VideoGenerator(source['url'], source['id'], source['priority'],
                                             scheduler_address, task_manage_address,
                                             controller_port, source['resolution'],
                                             source['fps'])
        elif data_modal == 'audio':
            generator = AudioGenerator()
        elif data_modal == 'imu':
            generator = IMUGenerator()
        else:
            assert None, 'Invalid data modal!'

        threading.Thread(target=generator.run).start()


if __name__ == '__main__':
    main()
