import abc


class BaseBSOperation(metaclass=abc.ABCMeta):
    def __call__(self, system):
        raise NotImplementedError
