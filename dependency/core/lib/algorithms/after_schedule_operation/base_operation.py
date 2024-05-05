import abc


class BaseASOperation(metaclass=abc.ABCMeta):
    def __call__(self, system, scheduler_response):
        raise NotImplementedError
