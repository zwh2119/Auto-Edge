import threading

from lib.common import ClassFactory, ClassType
from lib.common import YamlOps
from lib.common import FileNameConstant
from lib.common import Context
from lib.common import LOGGER


class GeneratorServer:

    def __init__(self):
        self.generator_list = []

    @staticmethod
    def read_config():
        try:
            file_path = Context.get_file_path(FileNameConstant.GENERATOR_CONFIG)
            data = YamlOps.read_yaml(file_path)
            assert type(data['data_source']) is list, 'Data source configs in file is not list!'
            return data['data_source']
        except Exception as e:
            LOGGER.warning(f'File {FileNameConstant.GENERATOR_CONFIG} open failed!')
            LOGGER.warning(e)

    def run(self):
        configs = self.read_config()
        for config in configs:
            generator = ClassFactory.get_cls(
                ClassType.GENERATOR,
                config['type']
            )(config['id'], config['pipeline'], config['url'], config['metadata'])

            self.generator_list.append(generator)

        for generator in self.generator_list:
            threading.Thread(target=generator.run).run()
