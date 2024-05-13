import abc


class BaseScenarioExtraction(metaclass=abc.ABCMeta):
    def __call__(self, task):
        raise NotImplementedError


