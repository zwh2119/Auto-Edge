import abc


class BaseStartupPolicy(metaclass=abc.ABCMeta):
    def __call__(self, info):
        raise NotImplementedError


