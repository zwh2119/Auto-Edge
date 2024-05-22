import abc

from core.lib.common import ClassFactory, ClassType, YamlOps, Context, FileNameConstant
from .base_config_extraction import BaseConfigExtraction

__all__ = ('HEIConfigExtraction',)


@ClassFactory.register(ClassType.SCH_CONFIG, alias='hei')
class HEIConfigExtraction(BaseConfigExtraction, abc.ABC):
    def __call__(self, scheduler):
        config_path = Context.get_file_path(FileNameConstant.SCHEDULE_CONFIG.value)
        configs = YamlOps.read_yaml(config_path)
        scheduler.fps_list = configs['fps']
        scheduler.resolution_list = configs['resolution']
        scheduler.buffer_size_list = configs['buffer_size']
        scheduler.schedule_knobs = ['resolution', 'fps', 'buffer_size', 'pipeline']

        drl_parameters_config_path = Context.get_file_path(FileNameConstant.HEI_DRL_CONFIG.value)
        scheduler.drl_params = YamlOps.read_yaml(drl_parameters_config_path)['drl_params']

        hyper_parameters_config_path = Context.get_file_path(FileNameConstant.HEI_HYPER_CONFIG.value)
        scheduler.hyper_params = YamlOps.read_yaml(hyper_parameters_config_path)['hyper_params']
