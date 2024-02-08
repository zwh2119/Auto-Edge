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
    SCHEDULE_CONFIG = ''
    GENERATOR_CONFIG = ''
