import abc


class BaseAgent(metaclass=abc.ABCMeta):
    def __call__(self):
        raise NotImplementedError

    def run(self, scheduler):
        raise NotImplementedError


