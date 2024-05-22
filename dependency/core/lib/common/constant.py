from enum import Enum


class AutoEdgeConstant(Enum):
    DEFAULT = 'auto-edge'

    GENERATOR = 'generator'
    CONTROLLER = 'controller'
    SCHEDULER = 'scheduler'
    DISTRIBUTOR = 'distributor'
    PROCESSOR = 'processor'
    MONITOR = 'monitor'


class FileNameConstant(Enum):
    SCHEDULE_CONFIG = 'scheduler_config.yaml'
    HEI_DRL_CONFIG = 'drl_parameters.yaml'
    HEI_HYPER_CONFIG = 'hyper_parameters.yaml'
    GENERATOR_CONFIG = 'generator_config.yaml'
    DISTRIBUTE_RECORD_DIR = 'record_data'
