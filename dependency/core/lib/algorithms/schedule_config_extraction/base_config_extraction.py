import abc


class BaseConfigExtraction(metaclass=abc.ABCMeta):
    def __call__(self, scheduler, config_path):
        raise NotImplementedError


