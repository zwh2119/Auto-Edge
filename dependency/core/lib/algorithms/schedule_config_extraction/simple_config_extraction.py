import abc

from core.lib.common import ClassFactory, ClassType, YamlOps
from .base_config_extraction import BaseConfigExtraction

__all__ = ('SimpleConfigExtraction',)


@ClassFactory.register(ClassType.SCH_CONFIG, alias='simple')
class SimpleConfigExtraction(BaseConfigExtraction, abc.ABC):
    def __call__(self, scheduler, config_path):
        configs = YamlOps.read_yaml(config_path)
        scheduler.fps_list = configs['fps']
        scheduler.resolution_list = configs['resolution']
        scheduler.buffer_size_list = configs['buffer_size']
