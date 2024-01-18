from log import LOGGER


class TaskTypeManager:
    def __init__(self, configs: list):
        self.configs = {}
        task_types = configs[0]['task_type']
        self.default_task_type = None
        for task_type in task_types:
            self.configs[task_type['type_name']] = task_type
            if task_type['default']:
                self.default_task_type = task_type['type_name']

        assert self.default_task_type, 'None default task type in config file'

        self.task_counter = {}
        for video_config in configs:
            self.task_counter[video_config['id']] = {'task_type': self.default_task_type, 'counter': 0}



