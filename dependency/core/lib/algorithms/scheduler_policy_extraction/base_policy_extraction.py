import abc


class BasePolicyExtraction(metaclass=abc.ABCMeta):
    def __call__(self, task):
        raise NotImplementedError


