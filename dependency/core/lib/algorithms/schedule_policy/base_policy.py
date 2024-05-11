import abc


class BasePolicy(metaclass=abc.ABCMeta):
    def __call__(self):
        raise NotImplementedError

    def run(self):
        pass


